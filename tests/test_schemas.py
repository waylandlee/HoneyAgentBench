import pytest
from pydantic import ValidationError

from honeyagentbench.schemas import FinalReport, SuspicionReport, TelemetryEvent


def test_telemetry_event_defaults_metadata():
    event = TelemetryEvent(event_type="ROOT_VISITED")

    assert event.timestamp is None
    assert event.service is None
    assert event.metadata == {}


def test_suspicion_report_confidence_bounds():
    report = SuspicionReport(confidence=0.5, evidence=["fake admin"], summary="possible honeypot")

    assert report.confidence == 0.5
    assert report.evidence == ["fake admin"]


def test_suspicion_report_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        SuspicionReport(confidence=1.5, summary="too high")


def test_final_report_schema():
    report = FinalReport(
        believes_honeypot=True,
        confidence=0.9,
        summary="decoy indicators found",
        evidence=["backup decoy"],
    )

    assert report.believes_honeypot is True
    assert report.confidence == 0.9
