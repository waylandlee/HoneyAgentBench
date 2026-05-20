"""Pydantic schemas used by telemetry, reports, and scoring."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    timestamp: float | None = None
    service: str | None = None
    event_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SuspicionReport(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    summary: str


class FinalReport(BaseModel):
    believes_honeypot: bool
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    evidence: list[str] = Field(default_factory=list)
