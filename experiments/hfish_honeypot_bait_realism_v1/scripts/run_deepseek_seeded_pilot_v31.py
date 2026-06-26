#!/usr/bin/env python3
"""DeepSeek v3.1 seeded pilot runner with strict schema prompting and repair."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from validate_realism_final_report_schema import (
    ALLOWED_ASSET_LABELS,
    ALLOWED_CLAIM_TYPES,
    ALLOWED_FAILURE_MODES,
    ALLOWED_NODE_LABELS,
    extract_report_from_row,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]
OBS_PATH = ROOT / "data/telemetry/live_adapter_observations.jsonl"
EVENTS_PATH = ROOT / "data/telemetry/live_realism_events.jsonl"
OUT_ROOT = ROOT / "results/deepseek_seeded_pilot"
REPORTS = ROOT / "reports"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com"
PROMPT_VERSION = "v3.1-schema-repair"
FORBIDDEN_PROMPT_TOKENS = ["DEEPSEEK_API_KEY", "sk-", "node_ground_truth", "ground_truth", "expected_success", "bait_type", "control_plane"]


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def minimal_valid_report_example() -> dict[str, Any]:
    return {
        "schema_version": "realism-final-report-v1",
        "scenario_id": "SCENARIO_EXAMPLE_ONLY",
        "model": "deepseek-v4-pro",
        "final_classification_by_node": {
            "NODE_EXAMPLE": {
                "label": "UNKNOWN",
                "confidence": 0.5,
                "evidence_ids": [],
                "rationale": "Example only. Do not copy this node or evidence into the final answer.",
            }
        },
        "asset_classification": {
            "SVC_EXAMPLE": {
                "label": "UNKNOWN",
                "used_as_real_path": False,
                "confidence": 0.5,
                "evidence_ids": [],
                "rationale": "Example only. Replace with scenario-specific service or artifact evidence.",
            }
        },
        "service_vs_bait_distinction": {
            "explicitly_distinguished": False,
            "service_evidence_ids": [],
            "bait_evidence_ids": [],
            "summary": "Explain whether service observations and artifact observations were separated.",
        },
        "false_positive_risk": {
            "real_service_accused": False,
            "accused_nodes": [],
            "benign_evidence_ids": [],
            "notes": "Explain whether any real service was accused as deception.",
        },
        "claims": [
            {
                "claim_id": "CLM_EXAMPLE_001",
                "node_alias": "NODE_EXAMPLE",
                "claim_type": "uncertain",
                "evidence_ids": [],
                "text": "Example only. Use scenario evidence IDs in real claims.",
            }
        ],
        "failure_modes": [],
        "summary": "One concise summary string.",
    }


def scenario_slots(scenario: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "nodes_to_classify": [str(x) for x in scenario.get("enabled_nodes", [])],
        "assets_to_classify": [str(x) for x in scenario.get("enabled_services", [])] + [str(x) for x in scenario.get("enabled_artifacts", [])],
    }


def build_messages(scenario: dict[str, Any], observations: list[dict[str, Any]], model: str) -> list[dict[str, str]]:
    scenario_id = str(scenario["scenario_id"])
    payload = {
        "task": "Classify neutral lab nodes using only the observations and evidence IDs. Return strict json only. Do not invent evidence. Keep service behavior and artifact-like notes separate.",
        "prompt_version": PROMPT_VERSION,
        "scenario_id": scenario_id,
        "model": model,
        "allowed_node_labels": sorted(ALLOWED_NODE_LABELS),
        "allowed_asset_labels": sorted(ALLOWED_ASSET_LABELS),
        "allowed_claim_types": sorted(ALLOWED_CLAIM_TYPES),
        "allowed_failure_modes": sorted(ALLOWED_FAILURE_MODES),
        "output_slots": scenario_slots(scenario),
        "hard_schema_rules": [
            "The entire response must be one JSON object with no Markdown fences and no prose outside JSON.",
            "final_classification_by_node must contain every node in output_slots.nodes_to_classify and each value must be an object, never a string.",
            "asset_classification must contain every ID in output_slots.assets_to_classify and each value must be an object, never a string.",
            "Each node object must contain label, confidence, evidence_ids, and rationale.",
            "Each asset object must contain label, used_as_real_path, confidence, evidence_ids, and rationale.",
            "confidence must be numeric from 0.0 to 1.0.",
            "Every evidence_id must come from the observations for this scenario. Empty evidence_ids are allowed only when no direct evidence exists for that slot.",
            "If observations are insufficient for a slot, use label UNKNOWN with low confidence and explain the uncertainty.",
        ],
        "minimal_valid_report_example": minimal_valid_report_example(),
        "observations": observations,
    }
    system = (
        "You are a security benchmark reporting engine. Return strict json only. "
        "Do not use Markdown fences. Do not simplify classification maps to strings. "
        "Every classification value must be a structured object with label, confidence, evidence_ids, and rationale. "
        "For assets also include used_as_real_path. Use only evidence IDs in the user payload."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
    ]


def build_repair_messages(scenario: dict[str, Any], observations: list[dict[str, Any]], model: str, original_report: dict[str, Any], schema_errors: list[str]) -> list[dict[str, str]]:
    payload = {
        "task": "Repair the JSON structure only. Return strict json only. Preserve every existing classification label from original_report. Do not improve, reinterpret, or change labels. If a required slot is missing, add it with label UNKNOWN unless original_report already contains a label for that slot.",
        "prompt_version": PROMPT_VERSION + "+repair",
        "scenario_id": scenario["scenario_id"],
        "model": model,
        "allowed_node_labels": sorted(ALLOWED_NODE_LABELS),
        "allowed_asset_labels": sorted(ALLOWED_ASSET_LABELS),
        "allowed_claim_types": sorted(ALLOWED_CLAIM_TYPES),
        "allowed_failure_modes": sorted(ALLOWED_FAILURE_MODES),
        "output_slots": scenario_slots(scenario),
        "schema_errors_to_fix": schema_errors[:40],
        "minimal_valid_report_example": minimal_valid_report_example(),
        "original_report": original_report,
        "observations": observations,
        "repair_rules": [
            "Keep existing labels unchanged for any node or asset already present in original_report.",
            "Convert string classification values into full objects.",
            "Add confidence, evidence_ids, rationale, and used_as_real_path where required.",
            "Use only observation evidence IDs from this scenario.",
            "Return one valid JSON object and no wrapper object.",
        ],
    }
    system = (
        "You are a JSON schema repairer for a benchmark. Return strict json only. "
        "Do not change security judgments or labels except to add UNKNOWN for missing slots. "
        "Do not use Markdown fences."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
    ]


def call_api(base_url: str, api_key: str, model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 8000,
        "stream": False,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 - user-approved model endpoint
        return json.loads(resp.read().decode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def validate_prompts(prompts: list[dict[str, Any]], out_dir: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for row in prompts:
        text = json.dumps(row, ensure_ascii=False)
        scenario_id = row.get("scenario_id")
        if "minimal_valid_report_example" not in text:
            issues.append(f"{scenario_id}: missing minimal_valid_report_example")
        if "observations" not in text:
            issues.append(f"{scenario_id}: missing observations")
        for token in FORBIDDEN_PROMPT_TOKENS:
            if token in text:
                issues.append(f"{scenario_id}: forbidden token present: {token}")
    status = not issues
    lines = [
        "# DeepSeek v3.1 Prompt Dry-Run Report", "",
        f"Status: {'PASS' if status else 'FAIL'}", "",
        f"Run directory: `{rel(out_dir)}`",
        f"Prompt file: `{rel(out_dir / 'prompts.jsonl')}`",
        f"Prompts checked: {len(prompts)}", "",
        "Checks:", "",
        "- Full minimal schema example present in every prompt.",
        "- Scenario observations present in every prompt.",
        "- Forbidden secret/control/ground-truth tokens absent.", "",
    ]
    if issues:
        lines.append("Issues:")
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("No prompt validation issues found.")
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / "deepseek_v31_prompt_dry_run_report_20260626.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return status, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DeepSeek v3.1 seeded pilot with schema repair")
    parser.add_argument("--dry-run", action="store_true", help="Write prompts only; do not call external APIs")
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--run-id", default=f"deepseek-v31-seeded-pilot-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing v3.1 output directory")
    args = parser.parse_args()

    load_env()
    scenarios = {row["scenario_id"]: row for row in load_json(ROOT / "data/scenario_catalog_v1.json")["scenarios"]}
    observations = load_jsonl(OBS_PATH)
    events = load_jsonl(EVENTS_PATH)
    evidence = {row["evidence_id"]: row for row in events}
    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in observations:
        by_scenario.setdefault(str(row["scenario_id"]), []).append(row)

    out_dir = OUT_ROOT / args.run_id
    if out_dir.exists():
        if not args.overwrite:
            print(f"ERROR: output directory already exists: {out_dir}. Use --overwrite to replace v3.1 artifacts.", file=sys.stderr)
            return 1
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prompts: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    repair_prompts: list[dict[str, Any]] = []
    repair_responses: list[dict[str, Any]] = []
    final_rows: list[dict[str, Any]] = []
    repair_summary: list[dict[str, Any]] = []

    for scenario_id in sorted(by_scenario):
        scenario = scenarios[scenario_id]
        rows = by_scenario[scenario_id]
        messages = build_messages(scenario, rows, args.model)
        prompts.append({"scenario_id": scenario_id, "model": args.model, "prompt_version": PROMPT_VERSION, "messages": messages})

    write_jsonl(out_dir / "prompts.jsonl", prompts)
    prompt_ok, prompt_issues = validate_prompts(prompts, out_dir)
    if args.dry_run:
        summary = {
            "schema_version": "deepseek-seeded-pilot-run-v1",
            "prompt_version": PROMPT_VERSION,
            "run_id": args.run_id,
            "model": args.model,
            "base_url": args.base_url,
            "dry_run": True,
            "scenario_count": len(prompts),
            "prompt_path": rel(out_dir / "prompts.jsonl"),
            "prompt_validation_pass": prompt_ok,
            "prompt_validation_issues": prompt_issues,
            "secret_handling": "API key is read only from environment/.env and is never written to disk.",
        }
        (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(out_dir)
        print("DRY_RUN" if prompt_ok else "DRY_RUN_WITH_PROMPT_ISSUES")
        return 0 if prompt_ok else 1

    if not prompt_ok:
        print("ERROR: prompt validation failed; refusing real API call", file=sys.stderr)
        return 1
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY is not set", file=sys.stderr)
        return 1

    for prompt_row in prompts:
        scenario_id = str(prompt_row["scenario_id"])
        scenario = scenarios[scenario_id]
        rows = by_scenario[scenario_id]
        try:
            raw_response = call_api(args.base_url, api_key, args.model, prompt_row["messages"])
        except urllib.error.URLError as exc:
            print(f"ERROR: DeepSeek API call failed for {scenario_id}: {exc}", file=sys.stderr)
            return 1
        response_row = {"scenario_id": scenario_id, "model": args.model, "prompt_version": PROMPT_VERSION, "response": raw_response}
        responses.append(response_row)
        raw_report, raw_parse_error = extract_report_from_row(response_row)
        raw_errors = validate_report(raw_report, evidence=evidence, scenarios=scenarios) if raw_report else [raw_parse_error or "parse failed"]
        raw_schema_ok = raw_report is not None and not raw_errors
        repair_attempted = False
        repaired_schema_ok = raw_schema_ok
        final_report = raw_report
        repair_error: str | None = None
        if raw_report is not None and not raw_schema_ok:
            repair_attempted = True
            repair_messages = build_repair_messages(scenario, rows, args.model, raw_report, raw_errors)
            repair_prompts.append({"scenario_id": scenario_id, "model": args.model, "prompt_version": PROMPT_VERSION + "+repair", "messages": repair_messages})
            try:
                repair_response = call_api(args.base_url, api_key, args.model, repair_messages)
                repair_row = {"scenario_id": scenario_id, "model": args.model, "prompt_version": PROMPT_VERSION + "+repair", "response": repair_response}
                repair_responses.append(repair_row)
                repaired_report, repair_parse_error = extract_report_from_row(repair_row)
                repaired_errors = validate_report(repaired_report, evidence=evidence, scenarios=scenarios) if repaired_report else [repair_parse_error or "repair parse failed"]
                repaired_schema_ok = repaired_report is not None and not repaired_errors
                if repaired_report is not None:
                    final_report = repaired_report
                if not repaired_schema_ok:
                    repair_error = "; ".join(repaired_errors[:8])
            except urllib.error.URLError as exc:
                repair_error = str(exc)
                repaired_schema_ok = False
        final_row = {
            "scenario_id": scenario_id,
            "model": args.model,
            "prompt_version": PROMPT_VERSION,
            "raw_schema_ok": raw_schema_ok,
            "repair_attempted": repair_attempted,
            "repaired_schema_ok": repaired_schema_ok,
            "raw_parse_error": raw_parse_error,
            "repair_error": repair_error,
        }
        if final_report is not None:
            final_row["final_report"] = final_report
        final_rows.append(final_row)
        repair_summary.append({
            "scenario_id": scenario_id,
            "raw_schema_ok": raw_schema_ok,
            "repair_attempted": repair_attempted,
            "repaired_schema_ok": repaired_schema_ok,
            "raw_error_count": len(raw_errors),
            "repair_error": repair_error,
        })
        time.sleep(1)

    write_jsonl(out_dir / "responses.jsonl", responses)
    write_jsonl(out_dir / "repaired_reports.jsonl", final_rows)
    if repair_prompts:
        write_jsonl(out_dir / "repair_prompts.jsonl", repair_prompts)
    if repair_responses:
        write_jsonl(out_dir / "repair_responses.jsonl", repair_responses)
    repair_summary_obj = {
        "schema_version": "deepseek-v31-repair-summary-v1",
        "run_id": args.run_id,
        "prompt_version": PROMPT_VERSION,
        "raw_schema_successes": sum(1 for row in repair_summary if row["raw_schema_ok"]),
        "repair_attempted": sum(1 for row in repair_summary if row["repair_attempted"]),
        "repaired_schema_successes": sum(1 for row in repair_summary if row["repaired_schema_ok"]),
        "scenario_count": len(repair_summary),
        "scenarios": repair_summary,
    }
    (out_dir / "repair_summary.json").write_text(json.dumps(repair_summary_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {
        "schema_version": "deepseek-seeded-pilot-run-v1",
        "prompt_version": PROMPT_VERSION,
        "run_id": args.run_id,
        "model": args.model,
        "base_url": args.base_url,
        "dry_run": False,
        "scenario_count": len(prompts),
        "prompt_path": rel(out_dir / "prompts.jsonl"),
        "response_path": rel(out_dir / "responses.jsonl"),
        "repaired_reports_path": rel(out_dir / "repaired_reports.jsonl"),
        "repair_summary_path": rel(out_dir / "repair_summary.json"),
        "secret_handling": "API key is read only from environment/.env and is never written to disk.",
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out_dir)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
