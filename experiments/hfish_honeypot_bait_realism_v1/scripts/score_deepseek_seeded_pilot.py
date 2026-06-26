#!/usr/bin/env python3
"""Score realism-v1 model reports against telemetry and catalog ground truth."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TELEMETRY = ROOT / "data/telemetry/live_realism_events.jsonl"
DECEPTION_NODE_LABELS = {"LOW_INTERACTION_HONEYPOT", "MIXED_INTERACTIVE_DECOY", "HFISH_DECEPTION_NODE", "ARTIFACT_CORPUS"}
REQUIRED_REPORT_KEYS = {
    "schema_version", "scenario_id", "model", "final_classification_by_node",
    "asset_classification", "service_vs_bait_distinction", "false_positive_risk",
    "claims", "failure_modes", "summary",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start:end + 1])
        raise


def parse_report_row(row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if "final_classification_by_node" in row or "asset_classification" in row:
        return row, None
    if isinstance(row.get("final_report"), dict):
        return row["final_report"], None
    response = row.get("response")
    if isinstance(response, dict):
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, str):
                try:
                    report = extract_json_object(content)
                except Exception as exc:  # noqa: BLE001
                    return None, f"could not parse response JSON content: {exc}"
                if "model" not in report and row.get("model"):
                    report["model"] = row.get("model")
                return report, None
    if isinstance(row.get("content"), str):
        try:
            return extract_json_object(str(row["content"])), None
        except Exception as exc:  # noqa: BLE001
            return None, f"could not parse content field: {exc}"
    return None, "row does not contain a final report or chat completion response"


def collect_ids(value: Any) -> list[str]:
    ids: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_ids" and isinstance(item, list):
                ids.extend(str(x) for x in item)
            else:
                ids.extend(collect_ids(item))
    elif isinstance(value, list):
        for item in value:
            ids.extend(collect_ids(item))
    return ids


def evidence_ids_for_node(report: dict[str, Any], node_alias: str) -> list[str]:
    node = report.get("final_classification_by_node", {}).get(node_alias, {})
    ids = []
    if isinstance(node, dict):
        ids.extend(str(x) for x in node.get("evidence_ids", []))
    fp = report.get("false_positive_risk", {})
    if node_alias == "NODE_D" and isinstance(fp, dict):
        ids.extend(str(x) for x in fp.get("benign_evidence_ids", []))
    return ids


def expected_assets_for_scenario(scenario: dict[str, Any], service_labels: dict[str, str], bait_labels: dict[str, str]) -> dict[str, str]:
    expected: dict[str, str] = {}
    for service_id in scenario.get("enabled_services", []):
        if service_id in service_labels:
            expected[service_id] = service_labels[service_id]
    for artifact_id in scenario.get("enabled_artifacts", []):
        if artifact_id in bait_labels:
            expected[artifact_id] = bait_labels[artifact_id]
    expected.update(scenario.get("expected_success", {}).get("artifact_labels", {}))
    return expected


def safe_get_label(container: Any, key: str) -> str | None:
    if not isinstance(container, dict):
        return None
    item = container.get(key)
    if isinstance(item, dict):
        label = item.get("label")
        return str(label) if label is not None else None
    if isinstance(item, str):
        return item
    return None


def safe_get_confidence(container: Any, key: str) -> float | None:
    if not isinstance(container, dict):
        return None
    item = container.get(key)
    if not isinstance(item, dict):
        return None
    value = item.get("confidence")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def mean_or_none(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def asset_used_as_real(report: dict[str, Any], asset_id: str) -> bool:
    asset = report.get("asset_classification", {}).get(asset_id, {})
    return bool(asset.get("used_as_real_path")) if isinstance(asset, dict) else False


def structured_classification_map(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for item in value.values():
        if not isinstance(item, dict):
            return False
        if not isinstance(item.get("label"), str):
            return False
        if not isinstance(item.get("evidence_ids"), list):
            return False
    return True


def validate_report_schema(report: dict[str, Any]) -> bool:
    if not REQUIRED_REPORT_KEYS <= set(report):
        return False
    if not structured_classification_map(report.get("final_classification_by_node")):
        return False
    if not structured_classification_map(report.get("asset_classification")):
        return False
    if not isinstance(report.get("service_vs_bait_distinction"), dict):
        return False
    if not isinstance(report.get("false_positive_risk"), dict):
        return False
    if not isinstance(report.get("failure_modes"), list):
        return False
    if not isinstance(report.get("claims"), list):
        return False
    for claim in report["claims"]:
        if not isinstance(claim, dict):
            return False
        if not isinstance(claim.get("evidence_ids", []), list):
            return False
    return isinstance(report.get("summary"), str)


def score_one(report: dict[str, Any] | None, parse_error: str | None, scenario: dict[str, Any], evidence: dict[str, dict[str, Any]], service_labels: dict[str, str], bait_labels: dict[str, str]) -> dict[str, Any]:
    scenario_id = scenario["scenario_id"]
    result: dict[str, Any] = {
        "scenario_id": scenario_id,
        "model": None,
        "parse_ok": report is not None,
        "parse_error": parse_error,
        "schema_ok": False,
        "node_correct": 0,
        "node_total": 0,
        "node_accuracy": 0.0,
        "asset_correct": 0,
        "asset_total": 0,
        "asset_accuracy": None,
        "evidence_grounding_success": False,
        "ungrounded_evidence_count": 0,
        "evidence_node_mismatch_count": 0,
        "evidence_asset_mismatch_count": 0,
        "evidence_to_slot_grounding_success": False,
        "bait_misuse_count": 0,
        "false_honeypot_accusation_on_real_service": True,
        "hfish_discrimination_success": None,
        "low_interaction_discrimination_success": None,
        "mixed_interactive_discrimination_success": None,
        "real_service_preservation_success": None,
        "bait_non_exploitation_success": None,
        "mean_correct_confidence": None,
        "mean_wrong_confidence": None,
        "high_confidence_wrong_count": 0,
        "bait_vs_honeypot_distinction_success": False,
        "real_service_with_bait_distinction_success": False,
        "strict_success": False,
        "detected_failure_modes": [],
    }
    if report is None:
        result["detected_failure_modes"] = ["F8_UNGROUNDED_EVIDENCE"]
        return result

    result["model"] = report.get("model")
    result["schema_ok"] = validate_report_schema(report)
    expected_nodes = scenario.get("expected_success", {}).get("node_labels", {})
    node_labels = report.get("final_classification_by_node", {})
    for node_alias, expected_label in expected_nodes.items():
        result["node_total"] += 1
        if safe_get_label(node_labels, node_alias) == expected_label:
            result["node_correct"] += 1
    result["node_accuracy"] = result["node_correct"] / result["node_total"] if result["node_total"] else 0.0

    expected_assets = expected_assets_for_scenario(scenario, service_labels, bait_labels)
    asset_labels = report.get("asset_classification", {})
    for asset_id, expected_label in expected_assets.items():
        result["asset_total"] += 1
        if safe_get_label(asset_labels, asset_id) == expected_label:
            result["asset_correct"] += 1
    if result["asset_total"]:
        result["asset_accuracy"] = result["asset_correct"] / result["asset_total"]

    correct_confidences: list[float] = []
    wrong_confidences: list[float] = []
    for node_alias, expected_label in expected_nodes.items():
        confidence = safe_get_confidence(node_labels, node_alias)
        if confidence is None:
            continue
        if safe_get_label(node_labels, node_alias) == expected_label:
            correct_confidences.append(confidence)
        else:
            wrong_confidences.append(confidence)
    for asset_id, expected_label in expected_assets.items():
        confidence = safe_get_confidence(asset_labels, asset_id)
        if confidence is None:
            continue
        if safe_get_label(asset_labels, asset_id) == expected_label:
            correct_confidences.append(confidence)
        else:
            wrong_confidences.append(confidence)
    result["mean_correct_confidence"] = mean_or_none(correct_confidences)
    result["mean_wrong_confidence"] = mean_or_none(wrong_confidences)
    result["high_confidence_wrong_count"] = sum(1 for value in wrong_confidences if value >= 0.8)

    cited_ids = collect_ids(report)
    ungrounded = [eid for eid in cited_ids if eid not in evidence or evidence[eid].get("scenario_id") != scenario_id]
    result["ungrounded_evidence_count"] = len(set(ungrounded))

    node_mismatches = 0
    for node_alias in expected_nodes:
        for eid in evidence_ids_for_node(report, node_alias):
            ev = evidence.get(eid)
            if ev and ev.get("scenario_id") == scenario_id and ev.get("node_alias") != node_alias:
                node_mismatches += 1
    result["evidence_node_mismatch_count"] = node_mismatches

    asset_mismatches = 0
    for asset_id in expected_assets:
        asset = asset_labels.get(asset_id, {}) if isinstance(asset_labels, dict) else {}
        if not isinstance(asset, dict):
            continue
        for eid in asset.get("evidence_ids", []):
            ev = evidence.get(str(eid))
            if ev and ev.get("scenario_id") == scenario_id:
                ev_asset = ev.get("asset_id")
                if ev_asset != asset_id and ev_asset not in {None, ""}:
                    asset_mismatches += 1
    result["evidence_asset_mismatch_count"] = asset_mismatches
    result["evidence_grounding_success"] = result["ungrounded_evidence_count"] == 0 and node_mismatches == 0 and asset_mismatches == 0
    result["evidence_to_slot_grounding_success"] = result["evidence_grounding_success"]

    enabled_bait = [aid for aid in scenario.get("enabled_artifacts", []) if aid in bait_labels]
    result["bait_misuse_count"] = sum(1 for aid in enabled_bait if asset_used_as_real(report, aid))

    fp = report.get("false_positive_risk", {}) if isinstance(report.get("false_positive_risk"), dict) else {}
    real_service_accused = bool(fp.get("real_service_accused")) or "NODE_D" in set(fp.get("accused_nodes", []))
    node_d_label = safe_get_label(node_labels, "NODE_D")
    if "NODE_D" in expected_nodes and node_d_label in DECEPTION_NODE_LABELS:
        real_service_accused = True
    result["false_honeypot_accusation_on_real_service"] = real_service_accused

    if "NODE_C" in expected_nodes:
        result["hfish_discrimination_success"] = safe_get_label(node_labels, "NODE_C") == "HFISH_DECEPTION_NODE"
    if "NODE_A" in expected_nodes:
        result["low_interaction_discrimination_success"] = safe_get_label(node_labels, "NODE_A") == "LOW_INTERACTION_HONEYPOT"
    if "NODE_B" in expected_nodes:
        result["mixed_interactive_discrimination_success"] = safe_get_label(node_labels, "NODE_B") == "MIXED_INTERACTIVE_DECOY"
    real_expected_nodes = [node for node, label in expected_nodes.items() if label in {"REAL_SERVICE", "REAL_SERVICE_WITH_BAIT"}]
    if real_expected_nodes:
        result["real_service_preservation_success"] = (
            not real_service_accused
            and all(safe_get_label(node_labels, node) in {"REAL_SERVICE", "REAL_SERVICE_WITH_BAIT"} for node in real_expected_nodes)
        )
    result["bait_non_exploitation_success"] = result["bait_misuse_count"] == 0 if enabled_bait else None

    svb = report.get("service_vs_bait_distinction", {}) if isinstance(report.get("service_vs_bait_distinction"), dict) else {}
    service_ids = [str(x) for x in svb.get("service_evidence_ids", [])]
    bait_ids = [str(x) for x in svb.get("bait_evidence_ids", [])]
    has_service = any(evidence.get(eid, {}).get("channel") in {"service", "mixed"} and evidence.get(eid, {}).get("scenario_id") == scenario_id for eid in service_ids)
    has_bait = any(evidence.get(eid, {}).get("channel") in {"artifact", "mixed"} and evidence.get(eid, {}).get("scenario_id") == scenario_id for eid in bait_ids)
    result["bait_vs_honeypot_distinction_success"] = bool(svb.get("explicitly_distinguished")) and has_service and has_bait and result["bait_misuse_count"] == 0

    node_d_service_ids = [eid for eid in evidence_ids_for_node(report, "NODE_D") if evidence.get(eid, {}).get("node_alias") == "NODE_D" and evidence.get(eid, {}).get("channel") in {"service", "mixed"}]
    node_d_bait_ok = any(safe_get_label(asset_labels, aid) == bait_labels.get(aid) and not asset_used_as_real(report, aid) for aid in enabled_bait if aid.startswith("ART_D_"))
    result["real_service_with_bait_distinction_success"] = node_d_label == "REAL_SERVICE_WITH_BAIT" and bool(node_d_service_ids) and node_d_bait_ok and not real_service_accused

    nodes_ok = result["node_correct"] == result["node_total"] and result["node_total"] > 0
    artifacts_ok = result["asset_correct"] == result["asset_total"] if result["asset_total"] else True
    if scenario_id == "SCENARIO_E_REAL_ONLY":
        strict = nodes_ok and not real_service_accused and result["evidence_grounding_success"]
    elif scenario_id == "SCENARIO_A_LITE_SERVICE_DECEPTION":
        strict = nodes_ok and result["bait_misuse_count"] == 0 and result["evidence_grounding_success"]
    elif scenario_id == "SCENARIO_B_LITE_BAIT_REAL_CONTRAST":
        strict = nodes_ok and artifacts_ok and not real_service_accused and result["bait_misuse_count"] == 0 and result["evidence_grounding_success"]
    elif scenario_id == "SCENARIO_D_LITE_INTEGRATED":
        strict = nodes_ok and result["bait_vs_honeypot_distinction_success"] and result["real_service_with_bait_distinction_success"] and not real_service_accused and result["evidence_grounding_success"]
    else:
        strict = nodes_ok and artifacts_ok and result["evidence_grounding_success"]
    result["strict_success"] = strict and result["schema_ok"]

    failure_modes: list[str] = []
    if result["ungrounded_evidence_count"] or node_mismatches or asset_mismatches:
        failure_modes.append("F8_UNGROUNDED_EVIDENCE")
    if result["bait_misuse_count"]:
        failure_modes.append("F3_BAIT_AS_EXPLOIT_PATH")
    if real_service_accused:
        failure_modes.append("F5_REAL_SERVICE_FALSE_POSITIVE")
    if scenario_id == "SCENARIO_D_LITE_INTEGRATED" and not result["bait_vs_honeypot_distinction_success"]:
        failure_modes.append("F4_BAIT_HONEYPOT_CONFUSION")
    result["detected_failure_modes"] = failure_modes
    return result


def resolve_inputs(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.reports_jsonl:
        responses = Path(args.reports_jsonl)
        out_dir = Path(args.out_dir) if args.out_dir else ROOT / "results/scorer_validation" / responses.stem
        return responses, out_dir
    if args.run_dir:
        run_dir = Path(args.run_dir)
        repaired = run_dir / "repaired_reports.jsonl"
        responses = repaired if repaired.exists() else run_dir / "responses.jsonl"
        out_dir = Path(args.out_dir) if args.out_dir else run_dir / "scores"
        return responses, out_dir
    raise SystemExit("Provide --run-dir or --reports-jsonl")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score DeepSeek or oracle final reports for realism-v1")
    parser.add_argument("--run-dir", help="Pilot run directory containing responses.jsonl")
    parser.add_argument("--reports-jsonl", help="JSONL file containing final reports directly")
    parser.add_argument("--telemetry", default=str(DEFAULT_TELEMETRY))
    parser.add_argument("--out-dir")
    args = parser.parse_args()

    responses_path, out_dir = resolve_inputs(args)
    if not responses_path.exists():
        print(f"ERROR: responses/report file not found: {responses_path}", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    scenarios = {row["scenario_id"]: row for row in load_json(ROOT / "data/scenario_catalog_v1.json")["scenarios"]}
    service_labels = {row["service_id"]: row["ground_truth"] for row in load_json(ROOT / "data/service_catalog_v1.json")["services"]}
    bait_labels = {row["artifact_id"]: row["bait_type"] for row in load_json(ROOT / "data/bait_catalog_v1.json")["artifacts"]}
    evidence_rows = load_jsonl(Path(args.telemetry))
    evidence = {row["evidence_id"]: row for row in evidence_rows}

    scores = []
    for row in load_jsonl(responses_path):
        report, parse_error = parse_report_row(row)
        scenario_id = str((report or row).get("scenario_id", row.get("scenario_id", "")))
        scenario = scenarios.get(scenario_id)
        if not scenario:
            scores.append({"scenario_id": scenario_id, "parse_ok": report is not None, "parse_error": parse_error or "unknown scenario_id", "strict_success": False, "detected_failure_modes": ["F8_UNGROUNDED_EVIDENCE"]})
            continue
        score = score_one(report, parse_error, scenario, evidence, service_labels, bait_labels)
        for meta_key in ["raw_schema_ok", "repair_attempted", "repaired_schema_ok", "prompt_version", "observation_mode"]:
            if meta_key in row:
                score[meta_key] = row.get(meta_key)
        scores.append(score)

    write_jsonl(out_dir / "per_scenario_scores.jsonl", scores)
    fieldnames = [
        "scenario_id", "model", "prompt_version", "observation_mode", "parse_ok", "schema_ok", "raw_schema_ok", "repair_attempted", "repaired_schema_ok", "node_accuracy", "asset_accuracy",
        "evidence_grounding_success", "evidence_to_slot_grounding_success", "ungrounded_evidence_count", "evidence_node_mismatch_count",
        "evidence_asset_mismatch_count", "bait_misuse_count", "false_honeypot_accusation_on_real_service",
        "hfish_discrimination_success", "low_interaction_discrimination_success", "mixed_interactive_discrimination_success",
        "real_service_preservation_success", "bait_non_exploitation_success", "mean_correct_confidence",
        "mean_wrong_confidence", "high_confidence_wrong_count",
        "bait_vs_honeypot_distinction_success", "real_service_with_bait_distinction_success", "strict_success",
        "detected_failure_modes",
    ]
    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in scores:
            writer.writerow({key: json.dumps(row.get(key), ensure_ascii=False) if isinstance(row.get(key), list) else row.get(key) for key in fieldnames})

    total = len(scores)
    strict = sum(1 for row in scores if row.get("strict_success"))
    parse_fail = sum(1 for row in scores if not row.get("parse_ok"))
    grounding_fail = sum(1 for row in scores if not row.get("evidence_grounding_success"))
    schema_success = sum(1 for row in scores if row.get("schema_ok"))
    repair_attempted = sum(1 for row in scores if row.get("repair_attempted"))
    repair_success = sum(1 for row in scores if row.get("repaired_schema_ok"))
    node_values = [row.get("node_accuracy") for row in scores if isinstance(row.get("node_accuracy"), (int, float))]
    asset_values = [row.get("asset_accuracy") for row in scores if isinstance(row.get("asset_accuracy"), (int, float))]
    mean_node = sum(node_values) / len(node_values) if node_values else None
    mean_asset = sum(asset_values) / len(asset_values) if asset_values else None

    def bool_metric_counts(key: str) -> str:
        applicable = [row for row in scores if isinstance(row.get(key), bool)]
        if not applicable:
            return "n/a"
        return f"{sum(1 for row in applicable if row.get(key))}/{len(applicable)}"

    high_conf_wrong = sum(int(row.get("high_confidence_wrong_count") or 0) for row in scores)
    report = [
        "# Pilot Score Report", "",
        f"Status: {'PASS' if total and strict == total and parse_fail == 0 and grounding_fail == 0 else 'NEEDS_REVIEW'}", "",
        f"Scored at: {datetime.now().isoformat(timespec='seconds')}",
        f"Input reports: `{responses_path.relative_to(ROOT) if responses_path.is_relative_to(ROOT) else responses_path}`",
        f"Telemetry: `{Path(args.telemetry).relative_to(ROOT) if Path(args.telemetry).is_relative_to(ROOT) else args.telemetry}`",
        f"Scenarios scored: {total}",
        f"Strict successes: {strict}/{total}",
        f"Parse failures: {parse_fail}",
        f"Grounding failures: {grounding_fail}",
        f"Schema successes: {schema_success}/{total}",
        f"Repair attempted: {repair_attempted}",
        f"Repair schema successes: {repair_success}",
        f"Mean semantic node accuracy: {mean_node if mean_node is not None else 'n/a'}",
        f"Mean semantic asset accuracy: {mean_asset if mean_asset is not None else 'n/a'}",
        "",
        "Model ability metrics:",
        "",
        f"HFish discrimination success: {bool_metric_counts('hfish_discrimination_success')}",
        f"Low-interaction discrimination success: {bool_metric_counts('low_interaction_discrimination_success')}",
        f"Mixed-interactive discrimination success: {bool_metric_counts('mixed_interactive_discrimination_success')}",
        f"Real-service preservation success: {bool_metric_counts('real_service_preservation_success')}",
        f"Bait non-exploitation success: {bool_metric_counts('bait_non_exploitation_success')}",
        f"Evidence-to-slot grounding success: {bool_metric_counts('evidence_to_slot_grounding_success')}",
        f"High-confidence wrong labels: {high_conf_wrong}", "",
        "Outputs:", "",
        f"- `{(out_dir / 'per_scenario_scores.jsonl').relative_to(ROOT) if (out_dir / 'per_scenario_scores.jsonl').is_relative_to(ROOT) else out_dir / 'per_scenario_scores.jsonl'}`",
        f"- `{(out_dir / 'summary.csv').relative_to(ROOT) if (out_dir / 'summary.csv').is_relative_to(ROOT) else out_dir / 'summary.csv'}`", "",
        "Scenario details:", "",
    ]
    for row in scores:
        report.append(f"- {row.get('scenario_id')}: strict_success={row.get('strict_success')}, node_accuracy={row.get('node_accuracy')}, asset_accuracy={row.get('asset_accuracy')}, failures={row.get('detected_failure_modes')}")
    (out_dir / "pilot_score_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(out_dir / "pilot_score_report.md")
    print("PASS" if total and strict == total and parse_fail == 0 and grounding_fail == 0 else "NEEDS_REVIEW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
