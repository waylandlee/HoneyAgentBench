from honeyagentbench.event_utils import append_jsonl, count_events, has_event, load_jsonl_events
from honeyagentbench.schemas import TelemetryEvent


def test_jsonl_roundtrip(tmp_path):
    path = tmp_path / "events.jsonl"
    append_jsonl(path, TelemetryEvent(event_type="ROOT_VISITED", service="web_honeypot"))
    append_jsonl(path, TelemetryEvent(event_type="DECOY_BACKUP_VISITED", service="web_honeypot"))

    events = load_jsonl_events(path)

    assert [event.event_type for event in events] == ["ROOT_VISITED", "DECOY_BACKUP_VISITED"]


def test_load_jsonl_skips_bad_lines(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"event_type":"ROOT_VISITED"}\nnot-json\n\n', encoding="utf-8")

    events = load_jsonl_events(path)

    assert len(events) == 1
    assert events[0].event_type == "ROOT_VISITED"


def test_count_and_has_event():
    events = [
        TelemetryEvent(event_type="ROOT_VISITED"),
        TelemetryEvent(event_type="DECOY_BACKUP_VISITED"),
    ]

    assert count_events(events) == 2
    assert count_events(events, {"ROOT_VISITED"}) == 1
    assert has_event(events, {"DECOY_BACKUP_VISITED"}) is True
    assert has_event(events, {"FINAL_REPORT_SUBMITTED"}) is False
