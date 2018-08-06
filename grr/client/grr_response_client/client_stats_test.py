#!/usr/bin/env python
import collections
import itertools

from builtins import range  # pylint: disable=redefined-builtin
import mock
import psutil

import unittest
from grr_response_client import client_stats
from grr_response_client.client_actions import admin
from grr_response_core import config
from grr_response_core.lib import rdfvalue
from grr_response_core.lib import stats
from grr.test_lib import test_lib


class ClientStatsCollectorTest(unittest.TestCase):

  @mock.patch.object(stats, "STATS")
  @mock.patch.object(admin, "GetClientStatsAuto")
  def testRealSamples(self, STATS, GetClientStatsAuto):  # pylint: disable=invalid-name
    del STATS  # Unused.
    del GetClientStatsAuto  # Unused.

    worker = mock.MagicMock()
    collector = client_stats.ClientStatsCollector(worker)

    future = rdfvalue.RDFDatetime.FromHumanReadable("2033-09-01")
    with test_lib.FakeTimeline(thread=collector, now=future) as timeline:
      timeline.Run(duration=rdfvalue.Duration("25s"))

    cpu_samples = collector.CpuSamplesBetween(
        start_time=future, end_time=future + rdfvalue.Duration("25s"))
    io_samples = collector.IOSamplesBetween(
        start_time=future, end_time=future + rdfvalue.Duration("25s"))

    self.assertEqual(len(cpu_samples), 3)
    self.assertEqual(len(io_samples), 3)

  @mock.patch.object(stats, "STATS")
  @mock.patch.object(admin, "GetClientStatsAuto")
  def testFakeSamples(self, STATS, GetClientStatsAuto):  # pylint: disable=invalid-name
    del STATS  # Unused.
    del GetClientStatsAuto  # Unused.

    with MockCpuTimes(), MockIoCounters(), MockCpuPercent():
      collector = client_stats.ClientStatsCollector(mock.MagicMock())

      millennium = rdfvalue.RDFDatetime.FromHumanReadable("2000-01-01")
      with test_lib.FakeTimeline(thread=collector, now=millennium) as timeline:
        timeline.Run(duration=rdfvalue.Duration("25s"))

      cpu_samples = collector.CpuSamplesBetween(
          start_time=millennium, end_time=millennium + rdfvalue.Duration("25s"))
      io_samples = collector.IOSamplesBetween(
          start_time=millennium, end_time=millennium + rdfvalue.Duration("25s"))

    self.assertEqual(len(cpu_samples), 3)
    self.assertEqual(len(io_samples), 3)
    for i in range(3):
      expected_timestamp = millennium + rdfvalue.Duration("10s") * i

      cpu_sample = cpu_samples[i]
      self.assertEqual(cpu_sample.timestamp, expected_timestamp)
      self.assertEqual(cpu_sample.user_cpu_time, FAKE_CPU_TIMES[i].user)
      self.assertEqual(cpu_sample.system_cpu_time, FAKE_CPU_TIMES[i].system)
      self.assertEqual(cpu_sample.cpu_percent, FAKE_CPU_PERCENT[i])

      io_sample = io_samples[i]
      self.assertEqual(io_sample.timestamp, expected_timestamp)
      self.assertEqual(io_sample.read_bytes, FAKE_IO_COUNTERS[i].read_bytes)
      self.assertEqual(io_sample.write_bytes, FAKE_IO_COUNTERS[i].write_bytes)

  @mock.patch.object(stats, "STATS")
  @mock.patch.object(admin, "GetClientStatsAuto")
  def testSampleFiltering(self, STATS, GetClientStatsAuto):  # pylint: disable=invalid-name
    del STATS  # Unused.
    del GetClientStatsAuto  # Unused.

    collector = client_stats.ClientStatsCollector(mock.MagicMock())

    past = rdfvalue.RDFDatetime.FromHumanReadable("1980-01-01")
    with test_lib.FakeTimeline(thread=collector, now=past) as timeline:
      timeline.Run(duration=rdfvalue.Duration("30m"))

    cpu_samples = collector.CpuSamplesBetween(
        start_time=past + rdfvalue.Duration("10m") + rdfvalue.Duration("1s"),
        end_time=past + rdfvalue.Duration("20m"))

    self.assertEqual(len(cpu_samples), 60)
    for sample in cpu_samples:
      self.assertLess(past + rdfvalue.Duration("10m"), sample)
      self.assertGreaterEqual(past + rdfvalue.Duration("20m"), sample.timestamp)

    io_samples = collector.IOSamplesBetween(
        start_time=past + rdfvalue.Duration("1m") + rdfvalue.Duration("1s"),
        end_time=past + rdfvalue.Duration("2m"))

    self.assertEqual(len(io_samples), 6)
    for sample in io_samples:
      self.assertLess(past + rdfvalue.Duration("1m"), sample.timestamp)
      self.assertGreaterEqual(past + rdfvalue.Duration("2m"), sample.timestamp)

  @mock.patch.object(stats, "STATS")
  @mock.patch.object(admin, "GetClientStatsAuto")
  def testOldSampleCleanup(self, STATS, GetClientStatsAuto):  # pylint: disable=invalid-name
    del STATS  # Unused.
    del GetClientStatsAuto  # Unused.

    collector = client_stats.ClientStatsCollector(mock.MagicMock())

    epoch = rdfvalue.RDFDatetime.FromSecondsSinceEpoch(0)
    with test_lib.FakeTimeline(thread=collector, now=epoch) as timeline:
      timeline.Run(duration=rdfvalue.Duration("3h"))

    cpu_samples = collector.CpuSamplesBetween(
        start_time=epoch, end_time=epoch + rdfvalue.Duration("1h"))
    self.assertEqual(len(cpu_samples), 0)

    io_samples = collector.IOSamplesBetween(
        start_time=epoch + rdfvalue.Duration("30m"),
        end_time=epoch + rdfvalue.Duration("1h") + rdfvalue.Duration("50m"))
    self.assertEqual(len(io_samples), 0)

  @mock.patch.object(stats, "STATS")
  @mock.patch.object(config, "CONFIG")
  @mock.patch.object(admin.GetClientStatsAuto, "Send")
  def testSampleSending(self, Send, CONFIG, STATS):  # pylint: disable=invalid-name
    del CONFIG  # Unused.
    del STATS  # Unused.

    with MockCpuTimes(), MockIoCounters(), MockCpuPercent():
      worker = mock.MagicMock()
      collector = client_stats.ClientStatsCollector(worker)
      worker.stats_collector = collector
      worker.IsActive = lambda: False

      today = rdfvalue.RDFDatetime.FromHumanReadable("2018-03-14")
      with test_lib.FakeTimeline(thread=collector, now=today) as timeline:
        timeline.Run(duration=rdfvalue.Duration("10s"))

        self.assertTrue(Send.called)
        response = Send.call_args[0][0]

        self.assertTrue(response.HasField("cpu_samples"))
        self.assertTrue(response.HasField("io_samples"))

        self.assertEqual(len(response.cpu_samples), 1)
        self.assertEqual(len(response.io_samples), 1)

        self.assertEqual(response.cpu_samples[0].timestamp, today)
        self.assertEqual(response.cpu_samples[0].user_cpu_time,
                         FAKE_CPU_TIMES[0].user)
        self.assertEqual(response.cpu_samples[0].system_cpu_time,
                         FAKE_CPU_TIMES[0].system)
        self.assertEqual(response.cpu_samples[0].cpu_percent,
                         FAKE_CPU_PERCENT[0])

        self.assertEqual(response.cpu_samples[0].timestamp, today)
        self.assertEqual(response.io_samples[0].read_bytes,
                         FAKE_IO_COUNTERS[0].read_bytes)
        self.assertEqual(response.io_samples[0].write_bytes,
                         FAKE_IO_COUNTERS[0].write_bytes)

  @mock.patch.object(stats, "STATS")
  @mock.patch.object(config, "CONFIG")
  @mock.patch.object(admin.GetClientStatsAuto, "Send")
  def testMinSendInterval(self, Send, CONFIG, STATS):  # pylint: disable=invalid-name
    del CONFIG  # Unused.
    del STATS  # Unused.

    worker = mock.MagicMock()
    collector = client_stats.ClientStatsCollector(worker)
    worker.stats_collector = collector
    worker.IsActive = lambda: False

    with test_lib.FakeTimeline(thread=collector) as timeline:
      timeline.Run(duration=rdfvalue.Duration("15s"))
      self.assertTrue(Send.called)

      collector.RequestSend()

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("10s"))
      self.assertFalse(Send.called)

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("20s"))
      self.assertFalse(Send.called)

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("40s"))
      self.assertTrue(Send.called)

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("30s"))
      self.assertFalse(Send.called)

  @mock.patch.object(stats, "STATS")
  @mock.patch.object(config, "CONFIG")
  @mock.patch.object(admin.GetClientStatsAuto, "Send")
  def testMaxSendInterval(self, Send, CONFIG, STATS):  # pylint: disable=invalid-name
    del CONFIG  # Unused.
    del STATS  # Unused.

    worker = mock.MagicMock()
    collector = client_stats.ClientStatsCollector(worker)
    worker.stats_collector = collector
    worker.IsActive = lambda: False

    with test_lib.FakeTimeline(thread=collector) as timeline:
      timeline.Run(duration=rdfvalue.Duration("15s"))
      self.assertTrue(Send.called)

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("20s"))
      self.assertFalse(Send.called)

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("30m"))
      self.assertFalse(Send.called)

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("30m"))
      self.assertTrue(Send.called)

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("20m"))
      self.assertFalse(Send.called)

      collector.RequestSend()

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("5s"))
      self.assertTrue(Send.called)

  @mock.patch.object(stats, "STATS")
  @mock.patch.object(config, "CONFIG")
  @mock.patch.object(admin.GetClientStatsAuto, "Send")
  def testSendWhenWorkerIsActive(self, Send, CONFIG, STATS):  # pylint: disable=invalid-name
    del CONFIG  # Unused.
    del STATS  # Unused.

    worker = mock.MagicMock()
    collector = client_stats.ClientStatsCollector(worker)
    worker.stats_collector = collector

    with test_lib.FakeTimeline(thread=collector) as timeline:
      worker.IsActive = lambda: True

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("5s"))
      self.assertTrue(Send.called)

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("2m"))
      self.assertTrue(Send.called)

      worker.IsActive = lambda: False

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("30m"))
      self.assertFalse(Send.called)

      worker.IsActive = lambda: True

      Send.reset_mock()
      timeline.Run(duration=rdfvalue.Duration("5s"))
      self.assertTrue(Send.called)


def MockCpuTimes():
  cycled_fake_cpu_times = itertools.cycle(FAKE_CPU_TIMES)
  return mock.patch.object(
      psutil.Process, "cpu_times", side_effect=cycled_fake_cpu_times)


def MockIoCounters():
  cycled_fake_io_counters = itertools.cycle(FAKE_IO_COUNTERS)
  return mock.patch.object(
      psutil.Process, "io_counters", side_effect=cycled_fake_io_counters)


def MockCpuPercent():
  cycled_fake_cpu_percent = itertools.cycle(FAKE_CPU_PERCENT)
  return mock.patch.object(
      psutil.Process, "cpu_percent", side_effect=cycled_fake_cpu_percent)


pcputime = collections.namedtuple(  # pylint: disable=invalid-name
    "pcputime", ("user", "system"))
pio = collections.namedtuple(  # pylint: disable=invalid-name
    "pio", ("read_bytes", "write_bytes", "read_count", "write_count"))

FAKE_CPU_TIMES = [
    pcputime(user=0.1, system=0.5),
    pcputime(user=0.2, system=0.75),
    pcputime(user=0.3, system=1.5),
]

FAKE_IO_COUNTERS = [
    pio(read_bytes=42, write_bytes=11, read_count=11, write_count=5),
    pio(read_bytes=1024, write_bytes=512, read_count=133, write_count=74),
    pio(read_bytes=4096, write_bytes=768, read_count=421, write_count=95),
]

FAKE_CPU_PERCENT = [1.0, 2.0, 4.0]

if __name__ == "__main__":
  unittest.main()
