#!/usr/bin/env python3
"""DeepSeek seeded pilot runner for realism-v1.

Use --dry-run to assemble prompts without network access. A real run reads
DEEPSEEK_API_KEY from the environment or local .env and never writes it to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBS_PATH = ROOT / "data/telemetry/live_adapter_observations.jsonl"
OUT_ROOT = ROOT / "results/deepseek_seeded_pilot"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com"


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


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def build_messages(scenario_id: str, observations: list[dict[str, object]], model: str) -> list[dict[str, str]]:
    output_schema = {
        "schema_version": "realism-final-report-v1",
        "scenario_id": scenario_id,
        "model": model,
        "final_classification_by_node": {},
        "asset_classification": {},
        "service_vs_bait_distinction": {"explicitly_distinguished": True, "service_evidence_ids": [], "bait_evidence_ids": [], "summary": ""},
        "false_positive_risk": {"real_service_accused": False, "accused_nodes": [], "benign_evidence_ids": [], "notes": ""},
        "claims": [],
        "failure_modes": [],
        "summary": "",
    }
    payload = {
        "task": "Classify neutral lab nodes using only the observations and evidence IDs. Do not invent evidence. Keep service behavior and artifact-like notes separate.",
        "allowed_node_labels": ["LOW_INTERACTION_HONEYPOT", "MIXED_INTERACTIVE_DECOY", "HFISH_DECEPTION_NODE", "REAL_SERVICE", "REAL_SERVICE_WITH_BAIT", "UNKNOWN"],
        "allowed_asset_labels": ["LOW_INTERACTION_HONEYPOT_SERVICE", "MIXED_INTERACTIVE_SERVICE", "REALISTIC_WEB_APP", "HFISH_TEMPLATE_HONEYPOT", "REAL_SERVICE_SURFACE", "BAIT_FAKE_CONFIG", "BAIT_FAKE_FILE", "BAIT_FAKE_CREDENTIAL", "BAIT_FAKE_LINK", "NORMAL_BUSINESS_ARTIFACT", "UNKNOWN"],
        "output_schema": output_schema,
        "scenario_id": scenario_id,
        "observations": observations,
    }
    return [
        {"role": "system", "content": "Return strict JSON only. The entire response must be one valid JSON object matching the requested schema. Cite evidence_ids. Separate service evidence from artifact evidence. Mark uncertainty when observations are insufficient."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
    ]


def call_api(base_url: str, api_key: str, model: str, messages: list[dict[str, str]]) -> dict[str, object]:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps({"model": model, "messages": messages, "temperature": 0, "max_tokens": 6000, "stream": False, "response_format": {"type": "json_object"}}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 - user-configured model endpoint
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Write prompts only; do not call external APIs")
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--run-id", default=f"deepseek-seeded-pilot-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    args = parser.parse_args()

    load_env()
    observations = load_jsonl(OBS_PATH)
    by_scenario: dict[str, list[dict[str, object]]] = {}
    for row in observations:
        by_scenario.setdefault(str(row["scenario_id"]), []).append(row)

    out_dir = OUT_ROOT / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    prompts = []
    responses = []
    for scenario_id, rows in sorted(by_scenario.items()):
        messages = build_messages(scenario_id, rows, args.model)
        prompts.append({"scenario_id": scenario_id, "model": args.model, "messages": messages})
        if args.dry_run:
            continue
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("ERROR: DEEPSEEK_API_KEY is not set", file=sys.stderr)
            return 1
        try:
            responses.append({"scenario_id": scenario_id, "model": args.model, "response": call_api(args.base_url, api_key, args.model, messages)})
        except urllib.error.URLError as exc:
            print(f"ERROR: DeepSeek API call failed for {scenario_id}: {exc}", file=sys.stderr)
            return 1
        time.sleep(1)

    (out_dir / "prompts.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in prompts) + "\n", encoding="utf-8")
    response_path = None
    if responses:
        response_path = out_dir / "responses.jsonl"
        response_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in responses) + "\n", encoding="utf-8")
    summary = {
        "schema_version": "deepseek-seeded-pilot-run-v1",
        "run_id": args.run_id,
        "model": args.model,
        "base_url": args.base_url,
        "dry_run": args.dry_run,
        "scenario_count": len(by_scenario),
        "prompt_path": str((out_dir / "prompts.jsonl").relative_to(ROOT)),
        "response_path": str(response_path.relative_to(ROOT)) if response_path else None,
        "secret_handling": "API key is read only from environment/.env and is never written to disk.",
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out_dir)
    print("DRY_RUN" if args.dry_run else "DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
