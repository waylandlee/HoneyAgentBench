#!/usr/bin/env python3
"""Preflight gate for the DeepSeek seeded realism-v1 pilot."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "deepseek_seeded_pilot_preflight.md"

REQUIRED = {
    "reports/node_a_dionaea_smoke_report.md": "Status: PASS",
    "reports/node_b_cowrie_smoke_report.md": "Status: PASS",
    "reports/node_b_juice_smoke_report.md": "Status: PASS",
    "reports/node_c_hfish_client_smoke_report.md": "Status: PASS",
    "reports/hfish_server_smoke_report.md": "Status: PASS",
    "reports/offline_scorer_validation.md": "Status: PASS",
    "reports/live_adapter_validation.md": "Status: PASS",
    "results/scorer_validation/live_oracle_20260626/pilot_score_report.md": "Status: PASS",
}


def load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def has_env_key(name: str) -> bool:
    if os.environ.get(name):
        return True
    env_path = ROOT / ".env"
    if not env_path.exists():
        return False
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line.startswith(f"{name}=") and line.split("=", 1)[1].strip():
            return True
    return False


def main() -> int:
    completed: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []

    try:
        manifest = json.loads((ROOT / "configs/image_manifest_v1.lock").read_text(encoding="utf-8-sig"))
        missing = [name for name, spec in manifest.get("images", {}).items() if name != "adapter" and not spec.get("digest")]
        if missing:
            blockers.append("Image manifest lacks digests for: " + ", ".join(missing))
        else:
            completed.append("All planned non-adapter images have pinned digests.")
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"Image manifest could not be loaded: {exc}")

    for rel, snippet in REQUIRED.items():
        path = ROOT / rel
        if not path.exists():
            blockers.append(f"Missing required report: {rel}")
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        if snippet not in text:
            blockers.append(f"Required snippet not found in {rel}: {snippet}")
        else:
            completed.append(f"{rel} contains `{snippet}`.")

    events = load_jsonl(ROOT / "data/telemetry/live_realism_events.jsonl")
    observations = load_jsonl(ROOT / "data/telemetry/live_adapter_observations.jsonl")
    if not events or not observations:
        blockers.append("Live adapter outputs are missing; run scripts/realism_adapter_live.py first.")
    else:
        completed.append(f"Live adapter produced {len(events)} evidence events and {len(observations)} observations.")
        catalog_modes = sorted({str(row.get("source_mode")) for row in events if "catalog" in str(row.get("source_mode"))})
        if catalog_modes:
            warnings.append("Some observations are catalog/seed-plan backed rather than fully Docker-content backed: " + ", ".join(catalog_modes))

    if not has_env_key("DEEPSEEK_API_KEY"):
        blockers.append("DEEPSEEK_API_KEY is not set in the current environment or local .env file. Do not paste it into reports or commands.")
    else:
        completed.append("DEEPSEEK_API_KEY is available to runtime without being printed.")

    status = "BLOCKED" if blockers else "PASS_WITH_LIMITATIONS" if warnings else "PASS"
    body = ["# DeepSeek Seeded Pilot Preflight", "", f"Status: {status}", "", "Scope: local readiness gate only. This script does not call DeepSeek or any external API.", "", "Completed checks:", ""]
    body.extend(f"- {item}" for item in completed) if completed else body.append("- None yet.")
    if warnings:
        body.extend(["", "Warnings:", ""])
        body.extend(f"- {item}" for item in warnings)
    if blockers:
        body.extend(["", "Blockers:", ""])
        body.extend(f"- {item}" for item in blockers)
    body.extend(["", "Next action:", "", "- Resolve blockers before running `scripts/run_deepseek_seeded_pilot.py` without `--dry-run`.", "- If Docker reports a missing image or pull failure, stop and let the user manually download/tag the image."])
    REPORT.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(REPORT)
    print(status)
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
