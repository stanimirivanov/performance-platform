"""Unit tests for metric collectors."""

from unittest.mock import Mock

from perfeng.integration.collectors import (
    CompositeCollector,
    CpuCollector,
    DiskCollector,
    MemoryCollector,
    NetworkCollector,
)
from perfeng.integration.models import Snapshot


class FakePsutil:
    def __init__(
        self,
        cpu=42.0,
        mem_percent=70.0,
        mem_total=16 * 1024**3,
        mem_avail=4 * 1024**3,
        disk_percent=55.0,
        disk_total=100 * 1024**3,
        disk_used=55 * 1024**3,
    ):
        self.cpu = cpu
        self.mem_percent = mem_percent
        self.mem_total = mem_total
        self.mem_avail = mem_avail
        self.disk_percent = disk_percent
        self.disk_total = disk_total
        self.disk_used = disk_used
        self.net = Mock()

    def cpu_percent(self, interval=None):
        return self.cpu

    def virtual_memory(self):
        return Mock(percent=self.mem_percent, total=self.mem_total, available=self.mem_avail)

    def disk_usage(self, path):
        return Mock(percent=self.disk_percent, total=self.disk_total, used=self.disk_used)

    def net_io_counters(self):
        return self.net


class FakeCollector:
    def __init__(self, snapshots):
        self.snapshots = snapshots

    def collect(self):
        return self.snapshots


class TestCpuCollector:
    def test_collect(self):
        fake = FakePsutil(cpu=33.3)
        collector = CpuCollector(psutil_module=fake)
        snaps = collector.collect()
        assert len(snaps) == 1
        assert snaps[0].resource_type == "cpu"
        assert snaps[0].value_current == 33.3
        assert snaps[0].unit == "percent"


class TestMemoryCollector:
    def test_collect(self):
        fake = FakePsutil(mem_percent=80.0, mem_total=32 * 1024**3, mem_avail=8 * 1024**3)
        collector = MemoryCollector(psutil_module=fake)
        snaps = collector.collect()
        assert len(snaps) == 1
        assert snaps[0].resource_type == "memory"
        assert snaps[0].value_current == 80.0
        assert snaps[0].attributes["total"] == 32 * 1024**3
        assert snaps[0].attributes["available"] == 8 * 1024**3


class TestDiskCollector:
    def test_collect(self):
        fake = FakePsutil(disk_percent=90.0, disk_total=500 * 1024**3, disk_used=450 * 1024**3)
        collector = DiskCollector(path="/data", psutil_module=fake)
        snaps = collector.collect()
        assert len(snaps) == 1
        assert snaps[0].resource_type == "disk"
        assert snaps[0].value_current == 90.0
        assert snaps[0].attributes["path"] == "/data"
        assert snaps[0].attributes["total"] == 500 * 1024**3


class TestNetworkCollector:
    def test_first_collect_returns_empty(self):
        fake = FakePsutil()
        fake.net = Mock(bytes_sent=100, bytes_recv=200)
        collector = NetworkCollector(psutil_module=fake, time_source=lambda: 0.0)
        snaps = collector.collect()
        assert snaps == []

    def test_second_collect_calculates_rates(self):
        fake = FakePsutil()
        # Initial counters
        fake.net = Mock(bytes_sent=1000, bytes_recv=2000)
        # Use a mutable time
        times = [0.0, 1.0]
        collector = NetworkCollector(psutil_module=fake, time_source=lambda: times.pop(0))

        # First call (no previous)
        assert collector.collect() == []

        # Update counters and second call
        fake.net = Mock(bytes_sent=1500, bytes_recv=2600)
        snaps = collector.collect()

        assert len(snaps) == 2
        sent = next(s for s in snaps if s.attributes.get("direction") == "sent")
        recv = next(s for s in snaps if s.attributes.get("direction") == "recv")
        assert sent.value_current == 500.0
        assert recv.value_current == 600.0
        assert sent.unit == "bytes_per_second"
        assert recv.unit == "bytes_per_second"


class TestCompositeCollector:
    def test_collect_isolates_failures(self):
        good = FakeCollector(
            [
                Snapshot(
                    resource_type="cpu",
                    value_current=1.0,
                    unit="percent",
                    test_phase="steady",
                    attributes={},
                )
            ]
        )
        bad = Mock()
        bad.collect.side_effect = Exception("boom")
        composite = CompositeCollector([bad, good])
        snaps = composite.collect()
        assert len(snaps) == 1
        assert snaps[0].resource_type == "cpu"

    def test_collect_all(self):
        c1 = FakeCollector(
            [
                Snapshot(
                    resource_type="cpu",
                    value_current=1.0,
                    unit="percent",
                    test_phase="steady",
                    attributes={},
                )
            ]
        )
        c2 = FakeCollector(
            [
                Snapshot(
                    resource_type="memory",
                    value_current=2.0,
                    unit="percent",
                    test_phase="steady",
                    attributes={},
                )
            ]
        )
        composite = CompositeCollector([c1, c2])
        snaps = composite.collect()
        assert len(snaps) == 2
