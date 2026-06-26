#!/usr/bin/env python3
"""DeepSeek v3.2 model-ability runner."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import shutil
import sys
import time
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any

from run_deepseek_seeded_pilot_v31 import call_api, load_env, minimal_valid_report_example, scenario_slots
from validate_realism_final_report_schema import (
    ALLOWED_ASSET_LABELS,
    ALLOWED_CLAIM_TYPES,
    ALLOWED_FAILURE_MODES,
    ALLOWED_NODE_LABELS,
    extract_report_from_row,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data/telemetry/live_realism_events.jsonl"
OUT_ROOT = ROOT / "results/deepseek_seeded_pilot"
REPORTS = ROOT / "reports"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com"
PROMPT_VERSION_PREFIX = "v3.2-model-ability"
OBSERVATION_FILES = {
    "neutral_summary": ROOT / "data/telemetry/v32_neutral_summary_observations.jsonl",
    "summary_balanced": ROOT / "data/telemetry/v32_summary_balanced_observations.jsonl",
    "raw_interaction": ROOT / "data/telemetry/v32_raw_interaction_observations.jsonl",
    "raw_full": ROOT / "data/telemetry/v32_raw_full_observations.jsonl",
    "raw_balanced": ROOT / "data/telemetry/v32_raw_balanced_observations.jsonl",
}
FORBIDDEN_PROMPT_TOKENS = [
    "DEEPSEEK_API_KEY", "sk-", "node_ground_truth", "ground_truth", "expected_success",
    "bait_type", "control_plane", "control plane", "source_service", "raw_log_ref",
]
FORBIDDEN_OBSERVATION_FRAMING = ["honeypot", "hfish", "bait", "decoy", "fake", "credential", "control_plane", "control plane", "ground_truth"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def prompt_version(mode: str) -> str:
    return f"{PROMPT_VERSION_PREFIX}-{mode}"


def scenario_mode_notes(mode: str) -> list[str]:
    notes = [
        "The observations are fixed lab observations, not live internet access.",
        "It is valid to conclude that all nodes are ordinary, partially synthetic, mixed, or UNKNOWN if the evidence supports that.",
        "Do not assume the benchmark expects a suspicious classification.",
        "Separate service behavior from file/note content before assigning node-level labels.",
        "File/note text is not a usable path unless observations show successful use.",
    ]
    if "raw" in mode:
        notes.append("Raw mode exposes protocol/page/file snippets with minimal interpretation; infer cautiously from the evidence.")
    if "balanced" in mode:
        notes.append("Balanced mode intentionally limits evidence volume per node and evidence role.")
    return notes


def build_messages(scenario: dict[str, Any], observations: list[dict[str, Any]], model: str, mode: str) -> list[dict[str, str]]:
    payload = {
        "task": "Classify lab nodes and assets using only the supplied observations and evidence IDs. Return strict JSON only.",
        "prompt_version": prompt_version(mode),
        "observation_mode": mode,
        "scenario_id": scenario["scenario_id"],
        "model": model,
        "allowed_node_labels": sorted(ALLOWED_NODE_LABELS),
        "allowed_asset_labels": sorted(ALLOWED_ASSET_LABELS),
        "allowed_claim_types": sorted(ALLOWED_CLAIM_TYPES),
        "allowed_failure_modes": sorted(ALLOWED_FAILURE_MODES),
        "output_slots": scenario_slots(scenario),
        "anti_framing_rules": scenario_mode_notes(mode),
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
        "You are a neutral lab-observation classifier. Return strict JSON only. "
        "Do not use Markdown fences. Do not assume any expected class distribution. "
        "Every classification value must be a structured object with label, confidence, evidence_ids, and rationale. "
        "For assets also include used_as_real_path. Use only evidence IDs in the user payload."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)}]


def build_repair_messages(scenario: dict[str, Any], observations: list[dict[str, Any]], model: str, mode: str, original_report: dict[str, Any], schema_errors: list[str]) -> list[dict[str, str]]:
    payload = {
        "task": "Repair JSON structure only. Preserve every existing classification label from original_report. Do not improve or reinterpret labels.",
        "prompt_version": prompt_version(mode) + "+repair",
        "observation_mode": mode,
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
        "You are a JSON schema repairer for a benchmark. Return strict JSON only. "
        "Do not change security judgments or labels except to add UNKNOWN for missing slots. Do not use Markdown fences."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)}]


def validate_prompts(prompts: list[dict[str, Any]], out_dir: Path, mode: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for row in prompts:
        text = json.dumps(row, ensure_ascii=False)
        scenario_id = row.get("scenario_id")
        if "minimal_valid_report_example" not in text:
            issues.append(f"{scenario_id}: missing minimal_valid_report_example")
        if "observations" not in text:
            issues.append(f"{scenario_id}: missing observations")
        if "Do not assume any expected class distribution" not in text:
            issues.append(f"{scenario_id}: missing neutral anti-framing instruction")
        for token in FORBIDDEN_PROMPT_TOKENS:
            if token in text:
                issues.append(f"{scenario_id}: forbidden prompt token present: {token}")
        for message in row.get("messages", []):
            if message.get("role") == "user":
                payload = json.loads(message["content"])
                for obs in payload.get("observations", []):
                    lower = str(obs.get("observation", "")).lower()
                    leaks = [token for token in FORBIDDEN_OBSERVATION_FRAMING if token in lower]
                    if leaks:
                        issues.append(f"{scenario_id}: observation {obs.get('evidence_id')} leaks framing terms: {', '.join(sorted(set(leaks)))}")
    status = not issues
    report_name = f"deepseek_v32_{mode}_prompt_dry_run_report_20260626.md"
    lines = [
        f"# DeepSeek v3.2 Prompt Dry-Run Report ({mode})", "", f"Status: {'PASS' if status else 'FAIL'}", "",
        f"Run directory: `{rel(out_dir)}`", f"Prompt file: `{rel(out_dir / 'prompts.jsonl')}`",
        f"Prompts checked: {len(prompts)}", f"Observation mode: `{mode}`", "", "Checks:", "",
        "- Full minimal schema example present in every prompt.",
        "- Scenario observations present in every prompt.",
        "- Forbidden secret/control/ground-truth tokens absent.",
        "- Model-facing observations avoid configured framing terms.",
        "- Prompt includes neutral anti-framing instructions.", "",
    ]
    if issues:
        lines.append("Issues:")
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("No prompt validation issues found.")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / report_name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return status, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DeepSeek v3.2 model-ability pilot with neutral/raw evidence modes")
    parser.add_argument("--dry-run", action="store_true", help="Write prompts only; do not call external APIs")
    parser.add_argument("--observation-mode", choices=sorted(OBSERVATION_FILES), default="raw_balanced")
    parser.add_argument("--observations-jsonl", help="Optional observation JSONL override")
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--run-id", default=f"deepseek-v32-seeded-pilot-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing v3.2 output directory")
    parser.add_argument("--confirm-external-upload-v32", action="store_true", help="Required for non-dry-run v3.2 API calls because this sends newly transformed observations")
    args = parser.parse_args()
    load_env()
    obs_path = Path(args.observations_jsonl) if args.observations_jsonl else OBSERVATION_FILES[args.observation_mode]
    if not obs_path.exists():
        print(f"ERROR: observation file not found: {obs_path}. Run scripts/build_v32_model_ability_observations.py first.", file=sys.stderr)
        return 1
    if not args.dry_run and not args.confirm_external_upload_v32:
        print("ERROR: v3.2 uses newly transformed observations. Re-run with --confirm-external-upload-v32 only after explicit user approval for this content class.", file=sys.stderr)
        return 1
    scenarios = {row["scenario_id"]: row for row in load_json(ROOT / "data/scenario_catalog_v1.json")["scenarios"]}
    observations = load_jsonl(obs_path)
    events = load_jsonl(EVENTS_PATH)
    evidence = {row["evidence_id"]: row for row in events}
    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in observations:
        by_scenario.setdefault(str(row["scenario_id"]), []).append(row)
    out_dir = OUT_ROOT / args.run_id
    if out_dir.exists():
        if not args.overwrite:
            print(f"ERROR: output directory already exists: {out_dir}. Use --overwrite to replace v3.2 artifacts.", file=sys.stderr)
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
        messages = build_messages(scenario, rows, args.model, args.observation_mode)
        prompts.append({"scenario_id": scenario_id, "model": args.model, "prompt_version": prompt_version(args.observation_mode), "observation_mode": args.observation_mode, "observations_path": rel(obs_path), "messages": messages})
    write_jsonl(out_dir / "prompts.jsonl", prompts)
    prompt_ok, prompt_issues = validate_prompts(prompts, out_dir, args.observation_mode)
    if args.dry_run:
        summary = {
            "schema_version": "deepseek-seeded-pilot-run-v1",
            "prompt_version": prompt_version(args.observation_mode),
            "run_id": args.run_id,
            "model": args.model,
            "base_url": args.base_url,
            "dry_run": True,
            "observation_mode": args.observation_mode,
            "observations_path": rel(obs_path),
            "scenario_count": len(prompts),
            "prompt_path": rel(out_dir / "prompts.jsonl"),
            "prompt_validation_pass": prompt_ok,
            "prompt_validation_issues": prompt_issues,
            "external_upload_status": "not_performed",
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
        except (urllib.error.URLError, http.client.IncompleteRead, TimeoutError) as exc:
            print(f"ERROR: DeepSeek API call failed for {scenario_id}: {exc}", file=sys.stderr)
            return 1
        response_row = {"scenario_id": scenario_id, "model": args.model, "prompt_version": prompt_version(args.observation_mode), "observation_mode": args.observation_mode, "response": raw_response}
        responses.append(response_row)
        write_jsonl(out_dir / "responses.jsonl", responses)
        raw_report, raw_parse_error = extract_report_from_row(response_row)
        raw_errors = validate_report(raw_report, evidence=evidence, scenarios=scenarios) if raw_report else [raw_parse_error or "parse failed"]
        raw_schema_ok = raw_report is not None and not raw_errors
        repair_attempted = False
        repaired_schema_ok = raw_schema_ok
        final_report = raw_report
        repair_error: str | None = None
        if raw_report is not None and not raw_schema_ok:
            repair_attempted = True
            repair_messages = build_repair_messages(scenario, rows, args.model, args.observation_mode, raw_report, raw_errors)
            repair_prompts.append({"scenario_id": scenario_id, "model": args.model, "prompt_version": prompt_version(args.observation_mode) + "+repair", "observation_mode": args.observation_mode, "messages": repair_messages})
            try:
                repair_response = call_api(args.base_url, api_key, args.model, repair_messages)
                repair_row = {"scenario_id": scenario_id, "model": args.model, "prompt_version": prompt_version(args.observation_mode) + "+repair", "observation_mode": args.observation_mode, "response": repair_response}
                repair_responses.append(repair_row)
                write_jsonl(out_dir / "repair_responses.jsonl", repair_responses)
                repaired_report, repair_parse_error = extract_report_from_row(repair_row)
                repaired_errors = validate_report(repaired_report, evidence=evidence, scenarios=scenarios) if repaired_report else [repair_parse_error or "repair parse failed"]
                repaired_schema_ok = repaired_report is not None and not repaired_errors
                if repaired_report is not None:
                    final_report = repaired_report
                if not repaired_schema_ok:
                    repair_error = "; ".join(repaired_errors[:8])
            except (urllib.error.URLError, http.client.IncompleteRead, TimeoutError) as exc:
                repair_error = str(exc)
                repaired_schema_ok = False
        final_row = {"scenario_id": scenario_id, "model": args.model, "prompt_version": prompt_version(args.observation_mode), "observation_mode": args.observation_mode, "raw_schema_ok": raw_schema_ok, "repair_attempted": repair_attempted, "repaired_schema_ok": repaired_schema_ok, "raw_parse_error": raw_parse_error, "repair_error": repair_error}
        if final_report is not None:
            final_row["final_report"] = final_report
        final_rows.append(final_row)
        write_jsonl(out_dir / "repaired_reports.jsonl", final_rows)
        repair_summary.append({"scenario_id": scenario_id, "raw_schema_ok": raw_schema_ok, "repair_attempted": repair_attempted, "repaired_schema_ok": repaired_schema_ok, "raw_error_count": len(raw_errors), "repair_error": repair_error})
        time.sleep(1)
    write_jsonl(out_dir / "responses.jsonl", responses)
    write_jsonl(out_dir / "repaired_reports.jsonl", final_rows)
    if repair_prompts:
        write_jsonl(out_dir / "repair_prompts.jsonl", repair_prompts)
    if repair_responses:
        write_jsonl(out_dir / "repair_responses.jsonl", repair_responses)
    repair_summary_obj = {"schema_version": "deepseek-v32-repair-summary-v1", "run_id": args.run_id, "prompt_version": prompt_version(args.observation_mode), "observation_mode": args.observation_mode, "raw_schema_successes": sum(1 for row in repair_summary if row["raw_schema_ok"]), "repair_attempted": sum(1 for row in repair_summary if row["repair_attempted"]), "repaired_schema_successes": sum(1 for row in repair_summary if row["repaired_schema_ok"]), "scenario_count": len(repair_summary), "scenarios": repair_summary}
    (out_dir / "repair_summary.json").write_text(json.dumps(repair_summary_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {"schema_version": "deepseek-seeded-pilot-run-v1", "prompt_version": prompt_version(args.observation_mode), "run_id": args.run_id, "model": args.model, "base_url": args.base_url, "dry_run": False, "observation_mode": args.observation_mode, "observations_path": rel(obs_path), "scenario_count": len(prompts), "prompt_path": rel(out_dir / "prompts.jsonl"), "response_path": rel(out_dir / "responses.jsonl"), "repaired_reports_path": rel(out_dir / "repaired_reports.jsonl"), "repair_summary_path": rel(out_dir / "repair_summary.json"), "external_upload_status": "performed_after_explicit_v32_flag", "secret_handling": "API key is read only from environment/.env and is never written to disk."}
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out_dir)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
