"""Helper for running end-to-end tests."""
import collections
import getpass
import inspect
import logging
import os
import requests
import time
import unittest
import urlparse

from grr_api_client import api
from grr.lib import config_lib

from grr.server.grr_response_server import maintenance_utils
from grr_response_test.end_to_end_tests import test_base

# We need to import all test classes so they can be added in test_base.REGISTRY
# by their metaclass.
#
# pylint: disable=unused-import
from grr_response_test.end_to_end_tests import tests
# pylint: enable=unused-import


class E2ETestError(Exception):
  pass


class E2ETestRunner(object):
  """Runs end-to-end tests against clients using the GRR API.

  If running in an Appveyor VM, test results (along with error messages) will
  be streamed to Appveyor, and will be visible in the UI.
  """

  SUCCESS_RESULT = "[  OK  ]"
  FAILURE_RESULT = "[ FAIL ]"

  def __init__(self, api_endpoint="", api_user="", api_password="",
      whitelisted_tests=None, upload_test_binaries=True,
      api_retry_period_secs=30, api_retry_deadline_secs=500):
    self._api_endpoint = api_endpoint
    self._api_user = api_user
    self._api_password = api_password
    self._whitelisted_tests = whitelisted_tests
    self._upload_test_binaries = upload_test_binaries
    self._api_retry_period_secs = api_retry_period_secs
    self._api_retry_deadline_secs = api_retry_deadline_secs
    self._grr_api = None
    self._appveyor_tests_endpoint = ""

  def Initialize(self):
    """Sets things up for running end-to-end tests.

    Only needs to be called once.
    """
    appveyor_api_url = os.environ.get("APPVEYOR_API_URL", None)
    if appveyor_api_url:
      logging.info("Using Appveyor API at %s", appveyor_api_url)
      self._appveyor_tests_endpoint = urlparse.urljoin(
          appveyor_api_url, "api/tests")

    logging.info("Connecting to API at %s", self._api_endpoint)
    password = self._api_password
    if not password:
      password = getpass.getpass(prompt="Please enter the API password for "
                                        "user '%s': " % self._api_user)
    self._grr_api = api.InitHttp(
        api_endpoint=self._api_endpoint, auth=(self._api_user, password))

    # Make sure binaries required by tests are uploaded to the datastore.
    if self._upload_test_binaries:
      server_paths = self._GetUploadedBinaries()
      if "hello" not in server_paths:
        self._UploadBinary("hello", "linux/test/hello")
      if "hello.exe" not in server_paths:
        self._UploadBinary("hello.exe", "windows/test/hello.exe")

  def _GetUploadedBinaries(self):
    start_time = time.time()
    while True:
      try:
        api_response = self._grr_api._context.SendRequest(
            "ListGrrBinaries", None)
        return {item.path for item in api_response.items}
      except requests.ConnectionError as e:
        if time.time() - start_time > self._api_retry_deadline_secs:
          logging.error("Timeout of %d seconds exceeded.",
                        self._api_retry_deadline_secs)
          raise
        logging.error(
            "Encountered error trying to connect to GRR API: %s" % e.args)
      logging.info("Retrying in %d seconds...", self._api_retry_period_secs)
      time.sleep(self._api_retry_period_secs)

  def _UploadBinary(self, bin_name, server_path):
    """Uploads a binary from the GRR installation dir to the datastore."""
    # TODO(ogaro): Upload binaries via the GRR API.
    logging.info("Uploading %s binary to server.", server_path)
    package_dir = config_lib.Resource().Filter(
        "grr_response_test@grr-response-test")
    with open(os.path.join(package_dir, "test_data", bin_name), "rb") as f:
      maintenance_utils.UploadSignedConfigBlob(
          f.read(), "aff4:/config/executables/%s" % server_path)

  def RunTestsAgainstClient(self, client_id):
    """Runs all applicable end-to-end tests against the given client."""
    client = self._GetClient(client_id)
    results = collections.OrderedDict()
    test_base.init_fn = lambda: (self._grr_api, client)
    unittest_runner = unittest.TextTestRunner()

    for test_name, test in self._GetApplicableTests(client).iteritems():
      start_time = time.time()
      result = unittest_runner.run(test)
      millis_elapsed = int((time.time() - start_time) * 1000)
      results[test_name] = result
      if not self._appveyor_tests_endpoint:
        continue

      assert_failures = ""
      unexpected_errors = ""
      appveyor_result_string = "Passed"
      if result.failures:
        appveyor_result_string = "Failed"
        assert_failures = "\n".join([msg for _, msg in result.failures])
      if result.errors:
        appveyor_result_string = "Failed"
        unexpected_errors = "\n".join([msg for _, msg in result.errors])
      resp = requests.post(self._appveyor_tests_endpoint, json={
        "testName": test_name,
        "testFramework": "JUnit",
        "outcome": appveyor_result_string,
        "durationMilliseconds": str(millis_elapsed),
        "fileName": os.path.basename(inspect.getsourcefile(test.__class__)),
        "ErrorMessage": assert_failures,
        "ErrorStackTrace": unexpected_errors,
      })
      logging.debug(
          "Uploaded results of %s to Appveyor. Response: %s", test_name, resp)

    # Print results.
    for line in self._GenerateReportLines(client_id, results):
      logging.info(line)

  def _GetClient(self, client_id):
    """Fetches the given client from the GRR API.

    If the client's platform is unknown, an Interrogate flow will be launched,
    and we will keep retrying until the platform is available. Having the
    platform available in the datastore is pre-requisite to many end-to-end
    tests.
    """
    start_time = time.time()
    def DeadlineExceeded():
      return time.time() - start_time > self._api_retry_deadline_secs
    interrogate_launched = False
    while True:
      try:
        client = self._grr_api.Client(client_id).Get()
        if client.data.os_info.system:
          return client
        if DeadlineExceeded():
          raise E2ETestError(
              "Timeout of %d seconds exceeded for %s.",
              self._api_retry_deadline_secs, client.client_id)
        logging.warning(
            "Platform for %s is not yet known to GRR.", client.client_id)
        if not interrogate_launched:
          interrogate_flow = client.CreateFlow(
              name="Interrogate",
              runner_args=self._grr_api.types.CreateFlowRunnerArgs())
          interrogate_launched = True
          logging.info("Launched Interrogate flow (%s) to retrieve system info "
                       "from %s.", interrogate_flow.flow_id, client.client_id)
      except requests.ConnectionError as e:
        if DeadlineExceeded():
          raise
        logging.error(
            "Encountered error trying to connect to GRR API: %s" % e.args)
      logging.info("Retrying in %d seconds...", self._api_retry_period_secs)
      time.sleep(self._api_retry_period_secs)

  def _GetApplicableTests(self, client):
    """Returns all e2e test methods that should be run against the client."""
    applicable_tests = {}
    for test_class in test_base.REGISTRY.values():
      if client.data.os_info.system not in test_class.platforms:
        continue
      test_suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
      for test in test_suite:
        test_name = "%s.%s" % (test_class.__name__, test._testMethodName)
        if (self._whitelisted_tests and
            test_class.__name__ not in self._whitelisted_tests and
            test_name not in self._whitelisted_tests):
          logging.debug("Skipping test %s for %s.", test_name, client.client_id)
        else:
          applicable_tests[test_name] = test
    return collections.OrderedDict(sorted(applicable_tests.iteritems()))

  def _GenerateReportLines(self, client_id, results_dict):
    """Summarizes test results for display in a terminal."""
    report_lines = []
    max_test_name_len = max([len(test_name) for test_name in results_dict])
    report_lines.append("Results for %s:" % client_id)
    for test_name, result in results_dict.iteritems():
      pretty_result = self.SUCCESS_RESULT
      if result.errors or result.failures:
        pretty_result = self.FAILURE_RESULT
      # Print a summary line for the test, using left-alignment for the test
      # name and right alignment for the result.
      report_lines.append(
          "\t%s %s" % (
              (test_name + ":").ljust(max_test_name_len + 1),
              pretty_result.rjust(10)))
    return report_lines
