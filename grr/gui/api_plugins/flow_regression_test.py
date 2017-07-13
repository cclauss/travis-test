#!/usr/bin/env python
"""This module contains regression tests for flows-related API handlers."""




from grr.gui import api_regression_test_lib
from grr.gui.api_plugins import flow as flow_plugin

from grr.lib import aff4
from grr.lib import flags
from grr.lib import flow
from grr.lib import output_plugin
from grr.lib import queue_manager
from grr.lib import rdfvalue
from grr.lib import test_lib
from grr.lib import utils
from grr.lib.flows.general import discovery
from grr.lib.flows.general import file_finder
from grr.lib.flows.general import processes
from grr.lib.flows.general import transfer
from grr.lib.hunts import standard_test
from grr.lib.output_plugins import email_plugin
from grr.lib.rdfvalues import client as rdf_client
from grr.lib.rdfvalues import flows as rdf_flows
from grr.lib.rdfvalues import paths as rdf_paths


class ApiGetFlowHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiGetFlowHandler."""

  api_method = "GetFlow"
  handler = flow_plugin.ApiGetFlowHandler

  def Run(self):
    # Fix the time to avoid regressions.
    with test_lib.FakeTime(42):
      client_urn = self.SetupClients(1)[0]

      # Delete the certificates as it's being regenerated every time the
      # client is created.
      with aff4.FACTORY.Open(
          client_urn, mode="rw", token=self.token) as client_obj:
        client_obj.DeleteAttribute(client_obj.Schema.CERT)

      flow_id = flow.GRRFlow.StartFlow(
          flow_name=discovery.Interrogate.__name__,
          client_id=client_urn,
          token=self.token)

      self.Check(
          "GetFlow",
          args=flow_plugin.ApiGetFlowArgs(
              client_id=client_urn.Basename(), flow_id=flow_id.Basename()),
          replace={flow_id.Basename(): "F:ABCDEF12"})


class ApiListFlowsHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Test client flows list handler."""

  api_method = "ListFlows"
  handler = flow_plugin.ApiListFlowsHandler

  def Run(self):
    with test_lib.FakeTime(42):
      client_urn = self.SetupClients(1)[0]

    with test_lib.FakeTime(43):
      flow_id_1 = flow.GRRFlow.StartFlow(
          flow_name=discovery.Interrogate.__name__,
          client_id=client_urn,
          token=self.token)

    with test_lib.FakeTime(44):
      flow_id_2 = flow.GRRFlow.StartFlow(
          flow_name=processes.ListProcesses.__name__,
          client_id=client_urn,
          token=self.token)

    self.Check(
        "ListFlows",
        args=flow_plugin.ApiListFlowsArgs(client_id=client_urn.Basename()),
        replace={
            flow_id_1.Basename(): "F:ABCDEF10",
            flow_id_2.Basename(): "F:ABCDEF11"
        })


class ApiListFlowRequestsHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiListFlowRequestsHandler."""

  api_method = "ListFlowRequests"
  handler = flow_plugin.ApiListFlowRequestsHandler

  def setUp(self):
    super(ApiListFlowRequestsHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):
    with test_lib.FakeTime(42):
      flow_urn = flow.GRRFlow.StartFlow(
          flow_name=processes.ListProcesses.__name__,
          client_id=self.client_id,
          token=self.token)

    mock = test_lib.MockClient(self.client_id, None, token=self.token)
    while mock.Next():
      pass

    replace = {flow_urn.Basename(): "W:ABCDEF"}

    manager = queue_manager.QueueManager(token=self.token)
    requests_responses = manager.FetchRequestsAndResponses(flow_urn)
    for request, responses in requests_responses:
      replace[str(request.request.task_id)] = "42"
      for response in responses:
        replace[str(response.task_id)] = "42"

    self.Check(
        "ListFlowRequests",
        args=flow_plugin.ApiListFlowRequestsArgs(
            client_id=self.client_id.Basename(), flow_id=flow_urn.Basename()),
        replace=replace)


class ApiListFlowResultsHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiListFlowResultsHandler."""

  api_method = "ListFlowResults"
  handler = flow_plugin.ApiListFlowResultsHandler

  def setUp(self):
    super(ApiListFlowResultsHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):
    runner_args = rdf_flows.FlowRunnerArgs(flow_name=transfer.GetFile.__name__)

    flow_args = transfer.GetFileArgs(pathspec=rdf_paths.PathSpec(
        path="/tmp/evil.txt", pathtype=rdf_paths.PathSpec.PathType.OS))

    client_mock = test_lib.SampleHuntMock()

    with test_lib.FakeTime(42):
      flow_urn = flow.GRRFlow.StartFlow(
          client_id=self.client_id,
          args=flow_args,
          runner_args=runner_args,
          token=self.token)

      for _ in test_lib.TestFlowHelper(
          flow_urn,
          client_mock=client_mock,
          client_id=self.client_id,
          token=self.token):
        pass

    self.Check(
        "ListFlowResults",
        args=flow_plugin.ApiListFlowResultsArgs(
            client_id=self.client_id.Basename(), flow_id=flow_urn.Basename()),
        replace={flow_urn.Basename(): "W:ABCDEF"})


class ApiListFlowLogsHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiListFlowResultsHandler."""

  api_method = "ListFlowLogs"
  handler = flow_plugin.ApiListFlowLogsHandler

  def setUp(self):
    super(ApiListFlowLogsHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):
    flow_urn = flow.GRRFlow.StartFlow(
        flow_name=processes.ListProcesses.__name__,
        client_id=self.client_id,
        token=self.token)

    with aff4.FACTORY.Open(flow_urn, mode="rw", token=self.token) as flow_obj:
      with test_lib.FakeTime(52):
        flow_obj.Log("Sample message: foo.")

      with test_lib.FakeTime(55):
        flow_obj.Log("Sample message: bar.")

    replace = {flow_urn.Basename(): "W:ABCDEF"}
    self.Check(
        "ListFlowLogs",
        args=flow_plugin.ApiListFlowLogsArgs(
            client_id=self.client_id.Basename(), flow_id=flow_urn.Basename()),
        replace=replace)
    self.Check(
        "ListFlowLogs",
        args=flow_plugin.ApiListFlowLogsArgs(
            client_id=self.client_id.Basename(),
            flow_id=flow_urn.Basename(),
            count=1),
        replace=replace)
    self.Check(
        "ListFlowLogs",
        args=flow_plugin.ApiListFlowLogsArgs(
            client_id=self.client_id.Basename(),
            flow_id=flow_urn.Basename(),
            count=1,
            offset=1),
        replace=replace)


class ApiGetFlowResultsExportCommandHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiGetFlowResultsExportCommandHandler."""

  api_method = "GetFlowResultsExportCommand"
  handler = flow_plugin.ApiGetFlowResultsExportCommandHandler

  def setUp(self):
    super(ApiGetFlowResultsExportCommandHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):
    with test_lib.FakeTime(42):
      flow_urn = flow.GRRFlow.StartFlow(
          flow_name=processes.ListProcesses.__name__,
          client_id=self.client_id,
          token=self.token)

    self.Check(
        "GetFlowResultsExportCommand",
        args=flow_plugin.ApiGetFlowResultsExportCommandArgs(
            client_id=self.client_id.Basename(), flow_id=flow_urn.Basename()),
        replace={flow_urn.Basename()[2:]: "ABCDEF"})


class ApiListFlowOutputPluginsHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiListFlowOutputPluginsHandler."""

  api_method = "ListFlowOutputPlugins"
  handler = flow_plugin.ApiListFlowOutputPluginsHandler

  # ApiOutputPlugin's state is an AttributedDict containing URNs that
  # are always random. Given that currently their JSON representation
  # is proto-serialized and then base64-encoded, there's no way
  # we can replace these URNs with something stable.
  uses_legacy_dynamic_protos = True

  def setUp(self):
    super(ApiListFlowOutputPluginsHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):
    email_descriptor = output_plugin.OutputPluginDescriptor(
        plugin_name=email_plugin.EmailOutputPlugin.__name__,
        plugin_args=email_plugin.EmailOutputPluginArgs(
            email_address="test@localhost", emails_limit=42))

    with test_lib.FakeTime(42):
      flow_urn = flow.GRRFlow.StartFlow(
          flow_name=processes.ListProcesses.__name__,
          client_id=self.client_id,
          output_plugins=[email_descriptor],
          token=self.token)

    self.Check(
        "ListFlowOutputPlugins",
        args=flow_plugin.ApiListFlowOutputPluginsArgs(
            client_id=self.client_id.Basename(), flow_id=flow_urn.Basename()),
        replace={flow_urn.Basename(): "W:ABCDEF"})


class ApiListFlowOutputPluginLogsHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiListFlowOutputPluginLogsHandler."""

  api_method = "ListFlowOutputPluginLogs"
  handler = flow_plugin.ApiListFlowOutputPluginLogsHandler

  # ApiOutputPlugin's state is an AttributedDict containing URNs that
  # are always random. Given that currently their JSON representation
  # is proto-serialized and then base64-encoded, there's no way
  # we can replace these URNs with something stable.
  uses_legacy_dynamic_protos = True

  def setUp(self):
    super(ApiListFlowOutputPluginLogsHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):
    email_descriptor = output_plugin.OutputPluginDescriptor(
        plugin_name=email_plugin.EmailOutputPlugin.__name__,
        plugin_args=email_plugin.EmailOutputPluginArgs(
            email_address="test@localhost", emails_limit=42))

    with test_lib.FakeTime(42):
      flow_urn = flow.GRRFlow.StartFlow(
          flow_name=test_lib.DummyFlowWithSingleReply.__name__,
          client_id=self.client_id,
          output_plugins=[email_descriptor],
          token=self.token)

    with test_lib.FakeTime(43):
      for _ in test_lib.TestFlowHelper(flow_urn, token=self.token):
        pass

    self.Check(
        "ListFlowOutputPluginLogs",
        args=flow_plugin.ApiListFlowOutputPluginLogsArgs(
            client_id=self.client_id.Basename(),
            flow_id=flow_urn.Basename(),
            plugin_id="EmailOutputPlugin_0"),
        replace={flow_urn.Basename(): "W:ABCDEF"})


class ApiListFlowOutputPluginErrorsHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiListFlowOutputPluginErrorsHandler."""

  api_method = "ListFlowOutputPluginErrors"
  handler = flow_plugin.ApiListFlowOutputPluginErrorsHandler

  # ApiOutputPlugin's state is an AttributedDict containing URNs that
  # are always random. Given that currently their JSON representation
  # is proto-serialized and then base64-encoded, there's no way
  # we can replace these URNs with something stable.
  uses_legacy_dynamic_protos = True

  def setUp(self):
    super(ApiListFlowOutputPluginErrorsHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):
    failing_descriptor = output_plugin.OutputPluginDescriptor(
        plugin_name=standard_test.FailingDummyHuntOutputPlugin.__name__)

    with test_lib.FakeTime(42):
      flow_urn = flow.GRRFlow.StartFlow(
          flow_name=test_lib.DummyFlowWithSingleReply.__name__,
          client_id=self.client_id,
          output_plugins=[failing_descriptor],
          token=self.token)

    with test_lib.FakeTime(43):
      for _ in test_lib.TestFlowHelper(flow_urn, token=self.token):
        pass

    self.Check(
        "ListFlowOutputPluginErrors",
        args=flow_plugin.ApiListFlowOutputPluginErrorsArgs(
            client_id=self.client_id.Basename(),
            flow_id=flow_urn.Basename(),
            plugin_id="FailingDummyHuntOutputPlugin_0"),
        replace={flow_urn.Basename(): "W:ABCDEF"})


class ApiCreateFlowHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiCreateFlowHandler."""

  api_method = "CreateFlow"
  handler = flow_plugin.ApiCreateFlowHandler

  def setUp(self):
    super(ApiCreateFlowHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):

    def ReplaceFlowId():
      flows_dir_fd = aff4.FACTORY.Open(
          self.client_id.Add("flows"), token=self.token)
      flow_urn = list(flows_dir_fd.ListChildren())[0]
      return {flow_urn.Basename(): "W:ABCDEF"}

    with test_lib.FakeTime(42):
      self.Check(
          "CreateFlow",
          args=flow_plugin.ApiCreateFlowArgs(
              client_id=self.client_id.Basename(),
              flow=flow_plugin.ApiFlow(
                  name=processes.ListProcesses.__name__,
                  args=processes.ListProcessesArgs(
                      filename_regex=".", fetch_binaries=True),
                  runner_args=rdf_flows.FlowRunnerArgs(
                      output_plugins=[],
                      priority="HIGH_PRIORITY",
                      notify_to_user=False))),
          replace=ReplaceFlowId)


class ApiCancelFlowHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiCancelFlowHandler."""

  api_method = "CancelFlow"
  handler = flow_plugin.ApiCancelFlowHandler

  def setUp(self):
    super(ApiCancelFlowHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):
    with test_lib.FakeTime(42):
      flow_urn = flow.GRRFlow.StartFlow(
          flow_name=processes.ListProcesses.__name__,
          client_id=self.client_id,
          token=self.token)

    self.Check(
        "CancelFlow",
        args=flow_plugin.ApiCancelFlowArgs(
            client_id=self.client_id.Basename(), flow_id=flow_urn.Basename()),
        replace={flow_urn.Basename(): "W:ABCDEF"})


class ApiListFlowDescriptorsHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Regression test for ApiListFlowDescriptorsHandler."""

  api_method = "ListFlowDescriptors"
  handler = flow_plugin.ApiListFlowDescriptorsHandler

  def Run(self):
    with utils.Stubber(flow.GRRFlow, "classes", {
        "ListProcesses": processes.ListProcesses,
        "FileFinder": file_finder.FileFinder,
    }):
      # RunReport flow is only shown for admins.
      self.CreateAdminUser("test")

      self.Check(
          "ListFlowDescriptors", args=flow_plugin.ApiListFlowDescriptorsArgs())
      self.Check(
          "ListFlowDescriptors",
          args=flow_plugin.ApiListFlowDescriptorsArgs(flow_type="CLIENT"))
      self.Check(
          "ListFlowDescriptors",
          args=flow_plugin.ApiListFlowDescriptorsArgs(flow_type="GLOBAL"))


class ApiStartRobotGetFilesOperationHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):

  api_method = "StartRobotGetFilesOperation"
  handler = flow_plugin.ApiStartRobotGetFilesOperationHandler

  def setUp(self):
    super(ApiStartRobotGetFilesOperationHandlerRegressionTest, self).setUp()
    self.client_id = self.SetupClients(1)[0]

  def Run(self):

    def ReplaceFlowId():
      flows_dir_fd = aff4.FACTORY.Open(
          self.client_id.Add("flows"), token=self.token)
      flow_urn = list(flows_dir_fd.ListChildren())[0]
      return {flow_urn.Basename(): "W:ABCDEF"}

    with test_lib.FakeTime(42):
      self.Check(
          "StartRobotGetFilesOperation",
          args=flow_plugin.ApiStartRobotGetFilesOperationArgs(
              hostname=self.client_id.Basename(), paths=["/tmp/test"]),
          replace=ReplaceFlowId)


class ApiGetRobotGetFilesOperationStateHandlerRegressionTest(
    api_regression_test_lib.ApiRegressionTest):
  """Test flow status handler.

  This handler is disabled by default in the ACLs so we need to do some
  patching to get the proper output and not just "access denied".
  """

  api_method = "GetRobotGetFilesOperationState"
  handler = flow_plugin.ApiGetRobotGetFilesOperationStateHandler

  def Run(self):
    # Fix the time to avoid regressions.
    with test_lib.FakeTime(42):
      self.SetupClients(1)

      start_handler = flow_plugin.ApiStartRobotGetFilesOperationHandler()
      start_args = flow_plugin.ApiStartRobotGetFilesOperationArgs(
          hostname="Host", paths=["/test"])
      start_result = start_handler.Handle(start_args, token=self.token)

      # Exploit the fact that 'get files' operation id is effectively a flow
      # URN.
      flow_urn = rdfvalue.RDFURN(start_result.operation_id)

      # Put something in the output collection
      collection = flow.GRRFlow.ResultCollectionForFID(
          flow_urn, token=self.token)
      collection.Add(rdf_client.ClientSummary())

      self.Check(
          "GetRobotGetFilesOperationState",
          args=flow_plugin.ApiGetRobotGetFilesOperationStateArgs(
              operation_id=start_result.operation_id),
          replace={flow_urn.Basename(): "F:ABCDEF12"})


def main(argv):
  api_regression_test_lib.main(argv)


if __name__ == "__main__":
  flags.StartMain(main)
