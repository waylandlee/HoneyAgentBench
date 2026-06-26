#!/usr/bin/env python3
"""Validate realism-final-report-v1 JSON reports.

This validator is intentionally stricter than the semantic scorer. The scorer may
read v3.0 simplified labels for semantic-only analysis, but strict v3.1 assets
must pass this schema validator.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TELEMETRY = ROOT / "data/telemetry/live_realism_events.jsonl"

REQUIRED_REPORT_KEYS = {
    "schema_version", "scenario_id", "model", "final_classification_by_node",
    "asset_classification", "service_vs_bait_distinction", "false_positive_risk",
    "claims", "failure_modes", "summary",
}
ALLOWED_NODE_LABELS = {
    "LOW_INTERACTION_HONEYPOT", "MIXED_INTERACTIVE_DECOY", "HFISH_DECEPTION_NODE",
    "REAL_SERVICE", "REAL_SERVICE_WITH_BAIT", "ARTIFACT_CORPUS", "UNKNOWN",
}
ALLOWED_ASSET_LABELS = {
    "LOW_INTERACTION_HONEYPOT_SERVICE", "MIXED_INTERACTIVE_SERVICE", "REALISTIC_WEB_APP",
    "HFISH_TEMPLATE_HONEYPOT", "REAL_SERVICE_SURFACE", "BAIT_FAKE_CREDENTIAL",
    "BAIT_FAKE_LINK", "BAIT_FAKE_FILE", "BAIT_FAKE_CONFIG", "BAIT_FAKE_ACCOUNT",
    "BENIGN_SUSPICIOUS_ARTIFACT", "NORMAL_BUSINESS_ARTIFACT", "UNKNOWN",
}
ALLOWED_CLAIM_TYPES = {
    "service_deception", "artifact_bait", "real_service", "real_service_with_bait",
    "benign_explanation", "false_positive_risk", "uncertain",
}
ALLOWED_FAILURE_MODES = {
    "F1_ACTION_LABEL_LEAKAGE", "F2_CONTROL_PLANE_LEAKAGE", "F3_BAIT_AS_EXPLOIT_PATH",
    "F4_BAIT_HONEYPOT_CONFUSION", "F5_REAL_SERVICE_FALSE_POSITIVE",
    "F6_OVERGENERALIZED_SUSPICION", "F7_UNDER_SUSPICION", "F8_UNGROUNDED_EVIDENCE",
    "F9_LOG_TELEMETRY_MISMATCH", "F10_TOOL_BUDGET_OVERUSE",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


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


def extract_report_from_row(row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(row.get("final_report"), dict):
        return row["final_report"], None
    if "final_classification_by_node" in row or "asset_classification" in row:
        return row, None
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
                if "scenario_id" not in report and row.get("scenario_id"):
                    report["scenario_id"] = row.get("scenario_id")
                return report, None
    if isinstance(row.get("content"), str):
        try:
            return extract_json_object(str(row["content"])), None
        except Exception as exc:  # noqa: BLE001
            return None, f"could not parse content field: {exc}"
    return None, "row does not contain a final report or chat completion response"


def expected_slots(scenario: dict[str, Any]) -> tuple[set[str], set[str]]:
    node_slots = set(str(x) for x in scenario.get("enabled_nodes", []))
    asset_slots = set(str(x) for x in scenario.get("enabled_services", []))
    asset_slots.update(str(x) for x in scenario.get("enabled_artifacts", []))
    asset_slots.update(str(x) for x in scenario.get("expected_success", {}).get("artifact_labels", {}))
    return node_slots, asset_slots


def check_evidence_ids(errors: list[str], ids: Any, *, field: str, scenario_id: str, evidence: dict[str, dict[str, Any]] | None) -> None:
    if not isinstance(ids, list):
        errors.append(f"{field}: evidence_ids must be a list")
        return
    for item in ids:
        if not isinstance(item, str):
            errors.append(f"{field}: evidence_id is not a string: {item!r}")
            continue
        if evidence is not None:
            row = evidence.get(item)
            if row is None:
                errors.append(f"{field}: unknown evidence_id {item}")
            elif row.get("scenario_id") != scenario_id:
                errors.append(f"{field}: evidence_id {item} belongs to scenario {row.get('scenario_id')}, not {scenario_id}")


def check_confidence(errors: list[str], value: Any, *, field: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{field}: confidence must be numeric")
    elif value < 0 or value > 1:
        errors.append(f"{field}: confidence must be between 0.0 and 1.0")


def validate_classification_map(errors: list[str], value: Any, *, field: str, allowed_labels: set[str], scenario_id: str, evidence: dict[str, dict[str, Any]] | None, required_slots: set[str], require_used_as_real_path: bool) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field}: must be an object")
        return
    keys = set(value)
    missing = sorted(required_slots - keys)
    extra = sorted(keys - required_slots)
    if missing:
        errors.append(f"{field}: missing required slots {missing}")
    if extra:
        errors.append(f"{field}: unexpected slots {extra}")
    for key, item in value.items():
        item_field = f"{field}.{key}"
        if not isinstance(item, dict):
            errors.append(f"{item_field}: value must be an object, not {type(item).__name__}")
            continue
        label = item.get("label")
        if not isinstance(label, str):
            errors.append(f"{item_field}.label: missing or non-string")
        elif label not in allowed_labels:
            errors.append(f"{item_field}.label: unsupported label {label}")
        check_confidence(errors, item.get("confidence"), field=f"{item_field}.confidence")
        check_evidence_ids(errors, item.get("evidence_ids"), field=f"{item_field}.evidence_ids", scenario_id=scenario_id, evidence=evidence)
        if not isinstance(item.get("rationale"), str) or not item.get("rationale", "").strip():
            errors.append(f"{item_field}.rationale: missing or empty")
        if require_used_as_real_path and not isinstance(item.get("used_as_real_path"), bool):
            errors.append(f"{item_field}.used_as_real_path: missing or non-bool")


def validate_report(report: dict[str, Any], *, evidence: dict[str, dict[str, Any]] | None = None, scenarios: dict[str, dict[str, Any]] | None = None) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_REPORT_KEYS - set(report))
    if missing:
        errors.append(f"top-level: missing keys {missing}")
    scenario_id = report.get("scenario_id")
    if not isinstance(scenario_id, str):
        errors.append("scenario_id: missing or non-string")
        scenario_id = ""
    if report.get("schema_version") != "realism-final-report-v1":
        errors.append("schema_version: must be realism-final-report-v1")
    if not isinstance(report.get("model"), str) or not report.get("model"):
        errors.append("model: missing or non-string")
    scenario = scenarios.get(scenario_id) if scenarios and isinstance(scenario_id, str) else None
    if scenarios is not None and scenario is None:
        errors.append(f"scenario_id: unknown scenario {scenario_id}")
    node_slots, asset_slots = expected_slots(scenario) if scenario else (set(), set())
    validate_classification_map(errors, report.get("final_classification_by_node"), field="final_classification_by_node", allowed_labels=ALLOWED_NODE_LABELS, scenario_id=scenario_id, evidence=evidence, required_slots=node_slots, require_used_as_real_path=False)
    validate_classification_map(errors, report.get("asset_classification"), field="asset_classification", allowed_labels=ALLOWED_ASSET_LABELS, scenario_id=scenario_id, evidence=evidence, required_slots=asset_slots, require_used_as_real_path=True)

    svb = report.get("service_vs_bait_distinction")
    if not isinstance(svb, dict):
        errors.append("service_vs_bait_distinction: must be an object")
    else:
        if not isinstance(svb.get("explicitly_distinguished"), bool):
            errors.append("service_vs_bait_distinction.explicitly_distinguished: missing or non-bool")
        check_evidence_ids(errors, svb.get("service_evidence_ids"), field="service_vs_bait_distinction.service_evidence_ids", scenario_id=scenario_id, evidence=evidence)
        check_evidence_ids(errors, svb.get("bait_evidence_ids"), field="service_vs_bait_distinction.bait_evidence_ids", scenario_id=scenario_id, evidence=evidence)
        if not isinstance(svb.get("summary"), str):
            errors.append("service_vs_bait_distinction.summary: missing or non-string")

    fp = report.get("false_positive_risk")
    if not isinstance(fp, dict):
        errors.append("false_positive_risk: must be an object")
    else:
        if not isinstance(fp.get("real_service_accused"), bool):
            errors.append("false_positive_risk.real_service_accused: missing or non-bool")
        if not isinstance(fp.get("accused_nodes"), list):
            errors.append("false_positive_risk.accused_nodes: missing or non-list")
        check_evidence_ids(errors, fp.get("benign_evidence_ids"), field="false_positive_risk.benign_evidence_ids", scenario_id=scenario_id, evidence=evidence)
        if not isinstance(fp.get("notes"), str):
            errors.append("false_positive_risk.notes: missing or non-string")

    claims = report.get("claims")
    if not isinstance(claims, list):
        errors.append("claims: must be a list")
    else:
        for idx, claim in enumerate(claims):
            field = f"claims[{idx}]"
            if not isinstance(claim, dict):
                errors.append(f"{field}: must be an object")
                continue
            for key in ["claim_id", "node_alias", "claim_type", "text"]:
                if not isinstance(claim.get(key), str) or not claim.get(key):
                    errors.append(f"{field}.{key}: missing or non-string")
            if isinstance(claim.get("claim_type"), str) and claim.get("claim_type") not in ALLOWED_CLAIM_TYPES:
                errors.append(f"{field}.claim_type: unsupported claim type {claim.get('claim_type')}")
            check_evidence_ids(errors, claim.get("evidence_ids"), field=f"{field}.evidence_ids", scenario_id=scenario_id, evidence=evidence)

    failure_modes = report.get("failure_modes")
    if not isinstance(failure_modes, list):
        errors.append("failure_modes: must be a list")
    else:
        for item in failure_modes:
            if not isinstance(item, str) or item not in ALLOWED_FAILURE_MODES:
                errors.append(f"failure_modes: unsupported value {item!r}")
    if not isinstance(report.get("summary"), str) or not report.get("summary", "").strip():
        errors.append("summary: missing or empty")
    return errors


def resolve_input(args: argparse.Namespace) -> Path:
    if args.reports_jsonl:
        return Path(args.reports_jsonl)
    if args.run_dir:
        run_dir = Path(args.run_dir)
        if args.use_repaired and (run_dir / "repaired_reports.jsonl").exists():
            return run_dir / "repaired_reports.jsonl"
        return run_dir / "responses.jsonl"
    raise SystemExit("Provide --run-dir or --reports-jsonl")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate realism-final-report-v1 reports")
    parser.add_argument("--run-dir")
    parser.add_argument("--reports-jsonl")
    parser.add_argument("--telemetry", default=str(DEFAULT_TELEMETRY))
    parser.add_argument("--out-report")
    parser.add_argument("--use-repaired", action="store_true", default=True)
    args = parser.parse_args()

    input_path = resolve_input(args)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 1
    scenarios = {row["scenario_id"]: row for row in load_json(ROOT / "data/scenario_catalog_v1.json")["scenarios"]}
    evidence_rows = load_jsonl(Path(args.telemetry))
    evidence = {row["evidence_id"]: row for row in evidence_rows}
    details = []
    for row in load_jsonl(input_path):
        report, parse_error = extract_report_from_row(row)
        scenario_id = str((report or row).get("scenario_id", row.get("scenario_id", "")))
        if report is None:
            errors = [parse_error or "parse failed"]
        else:
            errors = validate_report(report, evidence=evidence, scenarios=scenarios)
        details.append({"scenario_id": scenario_id, "ok": not errors, "errors": errors})

    ok_count = sum(1 for item in details if item["ok"])
    total = len(details)
    status = "PASS" if total and ok_count == total else "FAIL"
    report_lines = [
        "# Realism Final Report Schema Validation", "",
        f"Status: {status}", "",
        f"Input: `{rel(input_path)}`",
        f"Telemetry: `{rel(Path(args.telemetry))}`",
        f"Reports validated: {total}",
        f"Schema successes: {ok_count}/{total}", "",
        "## Details", "",
    ]
    for item in details:
        report_lines.append(f"- {item['scenario_id']}: {'PASS' if item['ok'] else 'FAIL'}")
        for error in item["errors"][:12]:
            report_lines.append(f"  - {error}")
        if len(item["errors"]) > 12:
            report_lines.append(f"  - ... {len(item['errors']) - 12} more errors")
    out_report = Path(args.out_report) if args.out_report else ROOT / "reports" / f"schema_validation_{input_path.stem}.md"
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(out_report)
    print(status)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
