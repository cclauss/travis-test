#!/usr/bin/env python
"""Helper script for running end-to-end tests."""

import getpass
import inspect
import logging
import os
import requests
import time
import unittest
import urlparse

# We need to import the server_plugins module before other server init modules.
# pylint: disable=unused-import,g-bad-import-order
from grr.server.grr_response_server import server_plugins
# pylint: disable=unused-import,g-bad-import-order

from grr import config
from grr_api_client import api
from grr.config import contexts
from grr.lib import config_lib
from grr.lib import flags
from grr.server.grr_response_server import access_control
from grr.server.grr_response_server import data_store
from grr.server.grr_response_server import maintenance_utils
from grr.server.grr_response_server import server_startup
from grr_response_test.end_to_end_tests import test_base
# pylint: disable=unused-import
from grr_response_test.end_to_end_tests import tests
# pylint: enable=unused-import

flags.DEFINE_string("api_endpoint", "http://localhost:8000",
                    "GRR API endpoint.")

flags.DEFINE_string("api_user", "admin", "Username for GRR API.")

flags.DEFINE_string("api_password", "", "Password for GRR API.")

flags.DEFINE_list("client_ids", [], "List of client ids to test.")

flags.DEFINE_list("hostnames", [], "List of client hostnames to test.")

flags.DEFINE_list(
    "testnames", [], "List of test cases to run. If unset we run all "
    "tests for a client's platform.")

flags.DEFINE_string("default_platform", "",
                    "Default client platform if it isn't known yet.")

# We use a logging Filter to exclude noisy unwanted log output.
flags.DEFINE_list("filenames_excluded_from_log", ["connectionpool.py"],
                  "Files whose log messages won't get printed.")

flags.DEFINE_bool("upload_test_binaries", True,
                  "Whether to upload executables needed by some e2e tests.")


class E2ETestError(Exception):
  pass


def RunEndToEndTests():
  """Runs end-to-end tests against clients using the GRR API."""

  ValidateAllTests()

  logging.info("Connecting to API at %s", flags.FLAGS.api_endpoint)
  password = flags.FLAGS.api_password
  if not password:
    password = getpass.getpass(prompt="Please enter the API password for "
                               "user '%s': " % flags.FLAGS.api_user)

  grr_api = api.InitHttp(
      api_endpoint=flags.FLAGS.api_endpoint,
      auth=(flags.FLAGS.api_user, password))

  target_clients = GetClients(grr_api)
  if not target_clients:
    raise RuntimeError(
        "No clients to test on. Either pass --client_ids or --hostnames "
        "or check that corresponding clients checked in recently.")

  # Make sure binaries required by tests are uploaded to the datastore.
  if flags.FLAGS.upload_test_binaries:
    api_response = grr_api._context.SendRequest("ListGrrBinaries", None)
    server_paths = {item.path for item in api_response.items}
    UploadBinaryIfAbsent(server_paths, "hello", "linux/test/hello")
    UploadBinaryIfAbsent(server_paths, "hello.exe", "windows/test/hello.exe")

  results_by_client = {}
  max_test_name_len = 0

  appveyor_tests_endpoint = None
  appveyor_api_url = os.environ.get("APPVEYOR_API_URL", None)
  if appveyor_api_url:
    appveyor_tests_endpoint = urlparse.urljoin(appveyor_api_url, "api/tests")

  logging.info("Running tests against %d clients...", len(target_clients))
  for client in target_clients:
    results_by_client[client.client_id] = RunTestsAgainstClient(
        grr_api, client, appveyor_tests_endpoint=appveyor_tests_endpoint)
    for test_name in results_by_client[client.client_id]:
      max_test_name_len = max(max_test_name_len, len(test_name))

  for client_urn, results in results_by_client.iteritems():
    logging.info("Results for %s:", client_urn)
    for test_name, result in sorted(results.items()):
      res = "[  OK  ]"
      if result.errors or result.failures:
        res = "[ FAIL ]"
      # Print a summary line for the test, using left-alignment for the test
      # name and right alignment for the result.
      logging.info("\t%s %s", (test_name + ":").ljust(max_test_name_len + 1),
                   res.rjust(10))


def GetClients(grr_api):
  tries_left = 10
  while tries_left > 0:
    tries_left -= 1
    try:
      return test_base.GetClientTestTargets(
          grr_api=grr_api,
          client_ids=flags.FLAGS.client_ids,
          hostnames=flags.FLAGS.hostnames)
    except requests.ConnectionError as e:
      logging.error(
          "Encountered error trying to connect to GRR API "
          "(%d tries left): %s" % (tries_left, e.args))
      if tries_left <= 0:
        raise
    time.sleep(5)


def ValidateAllTests():
  logging.info("Validating %d tests...", len(test_base.REGISTRY))
  for cls in test_base.REGISTRY.values():
    if not cls.platforms:
      raise ValueError(
          "%s: 'platforms' attribute can't be empty" % cls.__name__)

    for p in cls.platforms:
      if p not in test_base.EndToEndTest.Platform.ALL:
        raise ValueError(
            "Unsupported platform: %s in class %s" % (p, cls.__name__))


def UploadBinaryIfAbsent(server_paths, bin_name, server_path):
  if server_path in server_paths:
    return
  logging.info("Binary %s not uploaded yet. Will upload.", server_path)
  package_dir = config_lib.Resource().Filter(
      "grr_response_test@grr-response-test")
  with open(os.path.join(package_dir, "test_data", bin_name), "rb") as f:
    maintenance_utils.UploadSignedConfigBlob(
        f.read(), "aff4:/config/executables/%s" % server_path)


def RunTestsAgainstClient(grr_api, client, appveyor_tests_endpoint=None):
  """Runs all applicable end-to-end tests against a given client.

  Args:
      grr_api: GRR API connection.
      client: grr_api_client.Client
      appveyor_tests_endpoint: Appveyor API url (if running on Appveyor).

  Returns:
      A dict mapping test-methods to their results.

  Raises:
      RuntimeError: The client's platform isn't known to the GRR server.
  """
  client_platform = client.data.os_info.system
  if not client_platform:
    unknown_platform_msg = ("Unknown system type for client %s. Likely waiting "
        "on interrogate to complete." % client.client_id)
    if flags.FLAGS.default_platform:
      logging.warning(unknown_platform_msg)
      client_platform = flags.FLAGS.default_platform
    else:
      raise E2ETestError(unknown_platform_msg)

  results = {}
  test_base.init_fn = lambda: (grr_api, client)
  test_runner = unittest.TextTestRunner()
  for test_case in test_base.REGISTRY.values():
    if client_platform not in test_case.platforms:
      continue

    test_suite = unittest.TestLoader().loadTestsFromTestCase(test_case)
    tests_to_run = {}
    for test in test_suite:
      test_name = "%s.%s" % (test.__class__.__name__, test._testMethodName)
      if (flags.FLAGS.testnames and
          test_case.__name__ not in flags.FLAGS.testnames and
          test_name not in flags.FLAGS.testnames):
        logging.debug("Skipping test: %s", test_name)
        continue
      tests_to_run[test_name] = test

    tests_to_run = sorted(tests_to_run.iteritems())
    if appveyor_tests_endpoint:
      for test_name, test in tests_to_run:
        resp = requests.post(appveyor_tests_endpoint, json={
          "testName": test_name,
          "testFramework": "JUnit",
          "fileName": os.path.basename(inspect.getsourcefile(test.__class__)),
          "outcome": "None",
        })
        logging.debug("Added %s to Appveyor Tests API. Response: %s",
                      test_name, resp)

    for test_name, test in tests_to_run:
      if appveyor_tests_endpoint:
        resp = requests.put(appveyor_tests_endpoint, json={
          "testName": test_name,
          "outcome": "Running",
        })
        logging.debug("Changed status of %s to RUNNING. Response: %s",
                      test_name, resp)
      logging.info("Running %s on %s (%s)", test_name, client.client_id,
                   client_platform)
      start_time = time.time()
      result = test_runner.run(test)
      millis_elapsed = int((time.time() - start_time) * 1000)

      if appveyor_tests_endpoint:
        if result.errors or result.failures:
          text_result = "Failed"
        else:
          text_result = "Passed"
        resp = requests.put(appveyor_tests_endpoint, json={
            "testName": test_name,
            "outcome": text_result,
            "durationMilliseconds": str(millis_elapsed),
          })
        logging.debug("Set final status of %s. Response: %s", test_name, resp)
      results[test_name] = result
  return results


class E2ELogFilter(logging.Filter):
  """Logging filter that excludes log messages for particular files."""

  def filter(self, record):
    return record.filename not in flags.FLAGS.filenames_excluded_from_log


def main(argv):
  del argv  # Unused.
  config.CONFIG.AddContext(contexts.TEST_CONTEXT, "Context for running tests.")
  server_startup.Init()
  for handler in logging.getLogger().handlers:
    handler.addFilter(E2ELogFilter())
  data_store.default_token = access_control.ACLToken(
      username=getpass.getuser(), reason="End-to-end tests")
  return RunEndToEndTests()


if __name__ == "__main__":
  flags.StartMain(main)
