#!/usr/bin/env python
# -*- mode: python; encoding: utf-8 -*-
"""Test the vfs recursive refreshing functionality."""

import unittest
from grr.gui import gui_test_lib

from grr.lib import flags
from grr.lib.rdfvalues import client as rdf_client
from grr.server import aff4
from grr.test_lib import action_mocks
from grr.test_lib import fixture_test_lib
from grr.test_lib import flow_test_lib


class DirRecursiveRefreshTest(gui_test_lib.GRRSeleniumTest):

  def _RunUpdateFlow(self, client_id):
    # Get the flows that should have been started and finish them.
    fd = aff4.FACTORY.Open(client_id.Add("flows"), token=self.token)
    flows = list(fd.ListChildren())

    gui_test_lib.CreateFileVersion(
        client_id.Add("fs/os/c/a.txt"),
        "Hello World",
        timestamp=gui_test_lib.TIME_0,
        token=self.token)
    gui_test_lib.CreateFolder(
        client_id.Add("fs/os/c/TestFolder"),
        timestamp=gui_test_lib.TIME_0,
        token=self.token)
    gui_test_lib.CreateFolder(
        client_id.Add("fs/os/c/bin/TestBinFolder"),
        timestamp=gui_test_lib.TIME_0,
        token=self.token)

    client_mock = action_mocks.ActionMock()
    for flow_urn in flows:
      for _ in flow_test_lib.TestFlowHelper(
          flow_urn,
          client_mock,
          client_id=client_id,
          token=self.token,
          check_flow_errors=False):
        pass

  def setUp(self):
    super(DirRecursiveRefreshTest, self).setUp()
    # Prepare our fixture.
    self.client_id = rdf_client.ClientURN("C.0000000000000001")
    fixture_test_lib.ClientFixture(self.client_id, self.token)
    gui_test_lib.CreateFileVersions(self.token)
    self.RequestAndGrantClientApproval("C.0000000000000001")

  def testRecursiveRefreshButtonGetsDisabledWhileUpdateIsRunning(self):
    self.Open("/#/clients/C.0000000000000001/vfs/fs/os/c/")
    self.Click("css=button[name=RecursiveRefresh]:not([disabled])")

    self.Click("css=button[name=Proceed]")
    # The message should come and go (and the dialog should close itself).
    self.WaitUntil(self.IsTextPresent, "Refresh started successfully!")
    self.WaitUntilNot(self.IsTextPresent, "Refresh started successfully!")

    # Check that the button got disabled
    self.WaitUntil(self.IsElementPresent,
                   "css=button[name=RecursiveRefresh][disabled]")

    client_id = rdf_client.ClientURN("C.0000000000000001")
    self._RunUpdateFlow(client_id)

    # Ensure that refresh button is enabled again.
    #
    self.WaitUntilNot(self.IsElementPresent,
                      "css=button[name=RecursiveRefresh][disabled]")

  def testRecursiveRefreshButtonGetsReenabledWhenUpdateEnds(self):
    self.Open("/#/clients/C.0000000000000001/vfs/fs/os/c/")
    self.Click("css=button[name=RecursiveRefresh]:not([disabled])")

    self.Click("css=button[name=Proceed]")
    # The message should come and go (and the dialog should close itself).
    self.WaitUntil(self.IsTextPresent, "Refresh started successfully!")
    self.WaitUntilNot(self.IsTextPresent, "Refresh started successfully!")

    self.WaitUntil(self.IsElementPresent,
                   "css=button[name=RecursiveRefresh][disabled]")

    client_id = rdf_client.ClientURN("C.0000000000000001")
    self._RunUpdateFlow(client_id)

    # Check that the button got enabled again.
    self.WaitUntil(self.IsElementPresent,
                   "css=button[name=RecursiveRefresh]:not([disabled])")

  def testSwitchingFoldersReEnablesRecursiveRefreshButton(self):
    self.Open("/#/clients/C.0000000000000001/vfs/fs/os/c/")
    self.Click("css=button[name=RecursiveRefresh]:not([disabled])")

    self.Click("css=button[name=Proceed]")
    # The message should come and go (and the dialog should close itself).
    self.WaitUntil(self.IsTextPresent, "Refresh started successfully!")
    self.WaitUntilNot(self.IsTextPresent, "Refresh started successfully!")

    self.Click("css=#_fs-os-c-bin a")

    # Ensure that refresh button is enabled again.
    #
    self.WaitUntilNot(self.IsElementPresent,
                      "css=button[name=RecursiveRefresh][disabled]")

  def testTreeAndFileListRefreshedWhenRecursiveRefreshCompletes(self):
    self.Open("/#/clients/C.0000000000000001/vfs/fs/os/c/")
    self.Click("css=button[name=RecursiveRefresh]:not([disabled])")

    self.Click("css=button[name=Proceed]")
    # The message should come and go (and the dialog should close itself).
    self.WaitUntil(self.IsTextPresent, "Refresh started successfully!")
    self.WaitUntilNot(self.IsTextPresent, "Refresh started successfully!")

    client_id = rdf_client.ClientURN("C.0000000000000001")
    self._RunUpdateFlow(client_id)

    # The flow should be finished now, and file/tree lists update should
    # be triggered.
    # Ensure that the tree got updated as well as files list.
    self.WaitUntil(self.IsElementPresent, "css=tr:contains('TestFolder')")
    self.WaitUntil(self.IsElementPresent,
                   "css=#_fs-os-c-TestFolder i.jstree-icon")

  def testViewUpdatedWhenRecursiveUpdateCompletesAfterSelectionChange(self):
    self.Open("/#/clients/C.0000000000000001/vfs/fs/os/c/")
    self.Click("css=button[name=RecursiveRefresh]:not([disabled])")

    self.Click("css=button[name=Proceed]")
    # The message should come and go (and the dialog should close itself).
    self.WaitUntil(self.IsTextPresent, "Refresh started successfully!")
    self.WaitUntilNot(self.IsTextPresent, "Refresh started successfully!")

    # Change the selection while the update is in progress.
    self.WaitUntil(self.IsElementPresent,
                   "css=button[name=RecursiveRefresh][disabled]")
    self.Click("css=#_fs-os-c-bin a")

    client_id = rdf_client.ClientURN("C.0000000000000001")
    self._RunUpdateFlow(client_id)

    # The flow should be finished now, and directory tree update should
    # be triggered, even though the selection has changed during the update.
    #
    # Ensure that the tree got updated as well as files list.
    self.WaitUntil(self.IsElementPresent,
                   "css=#_fs-os-c-TestFolder i.jstree-icon")
    self.WaitUntil(self.IsElementPresent,
                   "css=#_fs-os-c-bin-TestBinFolder i.jstree-icon")

  def testRecursiveListDirectory(self):
    """Tests that Recursive Refresh button triggers correct flow."""
    self.Open("/")

    self.Type("client_query", "C.0000000000000001")
    self.Click("client_query_submit")

    self.WaitUntilEqual(u"C.0000000000000001", self.GetText,
                        "css=span[type=subject]")

    # Choose client 1
    self.Click("css=td:contains('0001')")

    # Go to Browse VFS
    self.Click("css=a[grrtarget='client.vfs']")
    self.Click("css=#_fs i.jstree-icon")
    self.Click("css=#_fs-os i.jstree-icon")
    self.Click("link=c")

    # Perform recursive refresh
    self.Click("css=button[name=RecursiveRefresh]:not([disabled])")

    self.WaitUntil(self.IsTextPresent, "Recursive Directory Refresh")
    self.WaitUntil(self.IsTextPresent, "Max depth")

    self.Type("css=label:contains('Max depth') ~ * input", "423")
    self.Click("css=button[name=Proceed]")

    self.WaitUntil(self.IsTextPresent, "Refresh started successfully!")
    self.WaitUntilNot(self.IsTextPresent, "Refresh started successfully!")

    # Go to "Manage Flows" tab and check that RecursiveListDirectory flow has
    # been created.
    self.Click("css=a[grrtarget='client.flows']")
    self.Click("css=td:contains('RecursiveListDirectory')")

    self.WaitUntil(self.IsElementPresent,
                   "css=.tab-content td.proto_value:contains('/c')")
    self.WaitUntil(self.IsElementPresent,
                   "css=.tab-content td.proto_value:contains(423)")


def main(argv):
  del argv  # Unused.
  # Run the full test suite
  unittest.main()


if __name__ == "__main__":
  flags.StartMain(main)
