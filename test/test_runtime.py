import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import runtime as runtime_module
from exporters.exporter import ExporterEvent
from runtime import Runtime


class _StopLoop(Exception):
    pass


class _RequestingExporter:
    """Asks for a new read of slot 0 while it is being notified, like a
    controller thread would during a slow webhook."""

    def __init__(self, runtime):
        self.runtime = runtime
        self.events = []

    def has_event(self, event):
        return True

    def export_data(self, scan, filament, reader):
        self.events.append(scan)
        if len(self.events) == 1:
            self.runtime.start_reading_tag(0)


@pytest.mark.parametrize("result", [
    ("scan", "filament"),  # TAG_READ
    ("scan", None),        # TAG_PARSE_ERROR
    (None, None),          # TAG_NOT_PRESENT
])
def test_request_during_export_is_kept(monkeypatch, result):
    rt = Runtime.__new__(Runtime)
    rt.config = SimpleNamespace(auto_read_mode=False, read_retries=3, read_interval_seconds=0)
    rt.rfid_readers = [SimpleNamespace(name="slot0")]
    exporter = _RequestingExporter(rt)
    rt.exporters = [exporter]
    rt.read_retries_left = [3]

    scan = SimpleNamespace(uid=b"\x01\x02\x03\x04") if result[0] else None
    rt.process_reader_single = lambda reader: (scan, result[1], False)

    def stop(_seconds):
        raise _StopLoop()
    monkeypatch.setattr(runtime_module.time, "sleep", stop)

    with pytest.raises(_StopLoop):
        rt.loop()

    assert len(exporter.events) == 1
    # The request made during the export is still pending for the next pass
    assert rt.read_retries_left[0] == 3
