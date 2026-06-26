#!/usr/bin/env python3
"""Offline adapter prototype for the realism extension.

The real M4 adapter will probe Docker services with fixed safe probes. This
prototype uses sample telemetry to validate the model-facing contract:
neutral action_id -> structured observation -> evidence_id.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data/telemetry/sample_realism_events.jsonl"
OUT_PATH = ROOT / "data/telemetry/offline_adapter_events.jsonl"
REPORT_PATH = ROOT / "reports/adapter_validation.md"

SCENARIO_ACTIONS = {
    "SCENARIO_E_REAL_ONLY": [
        "OBSERVE_NODE_D_HOME",
        "READ_NODE_D_COLLECTION_INDEX",
        "READ_NODE_D_MAINTENANCE_NOTE",
    ],
    "SCENARIO_D_LITE_INTEGRATED": [
        "OBSERVE_NODE_A_SERVICE_MAP",
        "OBSERVE_NODE_B_REMOTE_ACCESS_RESPONSE",
        "OBSERVE_NODE_B_WEB_HOME",
        "OBSERVE_NODE_C_SERVICE_SUMMARY",
        "READ_NODE_C_ARTIFACT_01",
        "OBSERVE_NODE_D_HOME",
        "READ_NODE_D_ARTIFACT_CANDIDATE",
    ],
}


def load_events():
    events = []
    for line in EVENTS_PATH.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def observe(events, scenario_id: str, action_id: str):
    matches = [
        row for row in events
        if row.get("scenario_id") == scenario_id and row.get("action_id_model_visible") == action_id
    ]
    if not matches:
        return {
            "status": "target_unavailable",
            "scenario_id": scenario_id,
            "action_id": action_id,
            "observation": "No sample observation is available for this neutral action in the offline adapter.",
            "evidence_id": None,
        }
    row = matches[0]
    return {
        "status": "ok",
        "scenario_id": scenario_id,
        "action_id": action_id,
        "node_alias": row["node_alias"],
        "channel": row["channel"],
        "asset_id": row["asset_id"],
        "evidence_id": row["evidence_id"],
        "observation": row["summary"],
    }


def main() -> int:
    events = load_events()
    outputs = []
    failures = []
    for scenario_id, actions in SCENARIO_ACTIONS.items():
        for action_id in actions:
            obs = observe(events, scenario_id, action_id)
            outputs.append(obs)
            if obs["status"] != "ok":
                failures.append(f"{scenario_id} {action_id} -> {obs['status']}")
    OUT_PATH.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in outputs) + "\n", encoding="utf-8")

    if failures:
        body = ["# Adapter Validation", "", "Status: FAIL", ""]
        body.extend(f"- {item}" for item in failures)
        REPORT_PATH.write_text("\n".join(body) + "\n", encoding="utf-8")
        print(REPORT_PATH)
        print("FAIL")
        return 1

    body = [
        "# Adapter Validation",
        "",
        "Status: PASS",
        "",
        "Validated offline adapter contract:",
        "",
        "- Neutral model-visible action IDs resolve to structured observations.",
        "- Each successful observation contains an evidence_id.",
        "- No raw IP, port, URL, shell command, or external probe is accepted by this prototype.",
        "- This validation did not start Docker services or call external model APIs.",
        "",
        f"Generated adapter events: `{OUT_PATH.relative_to(ROOT)}`",
    ]
    REPORT_PATH.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(REPORT_PATH)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
