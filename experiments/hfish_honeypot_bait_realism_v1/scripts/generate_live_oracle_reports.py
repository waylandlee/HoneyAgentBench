#!/usr/bin/env python3
"""Generate oracle final reports from current live telemetry for scorer validation."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data/telemetry/live_realism_events.jsonl"
OUT = ROOT / "data/telemetry/live_oracle_agent_reports.jsonl"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def ids(events, scenario_id, *, node=None, asset=None, channel=None):
    rows = []
    for ev in events:
        if ev.get("scenario_id") != scenario_id:
            continue
        if node and ev.get("node_alias") != node:
            continue
        if asset and ev.get("asset_id") != asset:
            continue
        if channel and ev.get("channel") not in channel:
            continue
        rows.append(ev["evidence_id"])
    return rows


def first_ids(events, scenario_id, asset_id):
    found = ids(events, scenario_id, asset=asset_id)
    if found:
        return found[:2]
    # Some summaries cite the representative service asset for a node. Use node evidence as fallback.
    for ev in events:
        if ev.get("scenario_id") == scenario_id and ev.get("asset_id") == asset_id:
            return [ev["evidence_id"]]
    return []


def main() -> int:
    events = load_jsonl(EVENTS)
    scenarios = load_json(ROOT / "data/scenario_catalog_v1.json")["scenarios"]
    service_labels = {row["service_id"]: row["ground_truth"] for row in load_json(ROOT / "data/service_catalog_v1.json")["services"]}
    bait_labels = {row["artifact_id"]: row["bait_type"] for row in load_json(ROOT / "data/bait_catalog_v1.json")["artifacts"]}
    reports = []
    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        expected_nodes = scenario["expected_success"].get("node_labels", {})
        final_nodes = {}
        for node_alias, label in expected_nodes.items():
            eids = ids(events, scenario_id, node=node_alias)[:4]
            final_nodes[node_alias] = {"label": label, "confidence": 0.9, "evidence_ids": eids, "rationale": "Oracle report generated from validated live telemetry."}

        asset_classification = {}
        for service_id in scenario.get("enabled_services", []):
            if service_id in service_labels:
                asset_classification[service_id] = {"label": service_labels[service_id], "used_as_real_path": False, "confidence": 0.9, "evidence_ids": first_ids(events, scenario_id, service_id), "rationale": "Oracle asset classification generated from validated live telemetry."}
        for artifact_id in scenario.get("enabled_artifacts", []):
            if artifact_id in bait_labels:
                asset_classification[artifact_id] = {"label": bait_labels[artifact_id], "used_as_real_path": False, "confidence": 0.9, "evidence_ids": first_ids(events, scenario_id, artifact_id), "rationale": "Oracle artifact classification generated from validated live telemetry."}
        asset_classification.update({
            aid: {"label": label, "used_as_real_path": False, "confidence": 0.9, "evidence_ids": first_ids(events, scenario_id, aid), "rationale": "Oracle expected artifact override generated from validated live telemetry."}
            for aid, label in scenario.get("expected_success", {}).get("artifact_labels", {}).items()
        })

        service_eids = ids(events, scenario_id, channel={"service", "mixed"})[:6]
        bait_eids = ids(events, scenario_id, channel={"artifact", "mixed"})[:6]
        distinguished = bool(bait_eids)
        report = {
            "schema_version": "realism-final-report-v1",
            "scenario_id": scenario_id,
            "model": "oracle-live-fixture",
            "final_classification_by_node": final_nodes,
            "asset_classification": asset_classification,
            "service_vs_bait_distinction": {
                "explicitly_distinguished": distinguished,
                "service_evidence_ids": service_eids if distinguished else [],
                "bait_evidence_ids": bait_eids if distinguished else [],
                "summary": "Oracle separates service evidence from artifact evidence." if distinguished else "No artifact evidence is enabled in this scenario.",
            },
            "false_positive_risk": {
                "real_service_accused": False,
                "accused_nodes": [],
                "benign_evidence_ids": ids(events, scenario_id, node="NODE_D", channel={"service", "mixed"})[:4],
                "notes": "Oracle does not accuse coherent real-service evidence.",
            },
            "claims": [
                {"claim_id": f"ORACLE_{scenario_id}_{idx:02d}", "node_alias": node, "claim_type": "real_service_with_bait" if label == "REAL_SERVICE_WITH_BAIT" else "real_service" if label == "REAL_SERVICE" else "service_deception", "evidence_ids": obj["evidence_ids"], "text": "Oracle claim grounded in live telemetry."}
                for idx, (node, label) in enumerate(expected_nodes.items(), start=1)
                for obj in [final_nodes[node]]
            ],
            "failure_modes": [],
            "summary": "Oracle report generated for scorer validation.",
        }
        reports.append(report)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in reports) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
