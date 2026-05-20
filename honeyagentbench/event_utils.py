"""Helpers for safe JSONL telemetry parsing and metric extraction."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

from honeyagentbench.schemas import TelemetryEvent


def now_timestamp() -> float:
    return time.time()


def append_jsonl(path: str | Path, event: TelemetryEvent) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(event.model_dump_json(exclude_none=True))
        handle.write("\n")


def load_jsonl_events(path: str | Path) -> list[TelemetryEvent]:
    target = Path(path)
    if not target.exists():
        return []

    return parse_jsonl_events(target.read_text(encoding="utf-8"))


def parse_jsonl_events(content: str) -> list[TelemetryEvent]:
    events: list[TelemetryEvent] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
            events.append(TelemetryEvent.model_validate(payload))
        except (json.JSONDecodeError, ValueError):
            continue
    return events


def load_many_jsonl(paths: Iterable[str | Path]) -> list[TelemetryEvent]:
    events: list[TelemetryEvent] = []
    for path in paths:
        events.extend(load_jsonl_events(path))
    return events


def count_events(events: Iterable[TelemetryEvent], event_types: set[str] | frozenset[str] | None = None) -> int:
    if event_types is None:
        return sum(1 for _ in events)
    return sum(1 for event in events if event.event_type in event_types)


def has_event(events: Iterable[TelemetryEvent], event_types: set[str] | frozenset[str]) -> bool:
    return any(event.event_type in event_types for event in events)


def first_event_index(events: list[TelemetryEvent], event_types: set[str] | frozenset[str]) -> int | None:
    for index, event in enumerate(events):
        if event.event_type in event_types:
            return index
    return None
