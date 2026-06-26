#!/usr/bin/env python3
"""Compare two scored realism-v1 runs with v3.2 model-ability metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ABILITY_KEYS = [
    "hfish_discrimination_success",
    "low_interaction_discrimination_success",
    "mixed_interactive_discrimination_success",
    "real_service_preservation_success",
    "bait_non_exploitation_success",
    "evidence_to_slot_grounding_success",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_scores(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_dir():
        candidate = path / "per_scenario_scores.jsonl"
        if candidate.exists():
            return candidate
        candidate = path / "scores/per_scenario_scores.jsonl"
        if candidate.exists():
            return candidate
    if path.exists():
        return path
    raise SystemExit(f"score input not found: {path_text}")


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def bool_count(rows: list[dict[str, Any]], key: str) -> str:
    applicable = [row for row in rows if isinstance(row.get(key), bool)]
    if not applicable:
        return "n/a"
    return f"{sum(1 for row in applicable if row.get(key))}/{len(applicable)}"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    node_values = [row.get("node_accuracy") for row in rows if isinstance(row.get("node_accuracy"), (int, float))]
    asset_values = [row.get("asset_accuracy") for row in rows if isinstance(row.get("asset_accuracy"), (int, float))]
    return {
        "scenarios": len(rows),
        "strict_success": f"{sum(1 for row in rows if row.get('strict_success'))}/{len(rows)}",
        "schema_success": f"{sum(1 for row in rows if row.get('schema_ok'))}/{len(rows)}",
        "grounding_success": f"{sum(1 for row in rows if row.get('evidence_grounding_success'))}/{len(rows)}",
        "mean_node_accuracy": mean(node_values),
        "mean_asset_accuracy": mean(asset_values),
        "high_confidence_wrong_count": sum(int(row.get("high_confidence_wrong_count") or 0) for row in rows),
        **{key: bool_count(rows, key) for key in ABILITY_KEYS},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two score outputs")
    parser.add_argument("--left", required=True, help="Left score dir or per_scenario_scores.jsonl")
    parser.add_argument("--right", required=True, help="Right score dir or per_scenario_scores.jsonl")
    parser.add_argument("--left-label", default="left")
    parser.add_argument("--right-label", default="right")
    parser.add_argument("--out", required=True, help="Markdown report path")
    args = parser.parse_args()

    left_path = resolve_scores(args.left)
    right_path = resolve_scores(args.right)
    left_rows = load_jsonl(left_path)
    right_rows = load_jsonl(right_path)
    left = summarize(left_rows)
    right = summarize(right_rows)

    keys = ["scenarios", "strict_success", "schema_success", "grounding_success", "mean_node_accuracy", "mean_asset_accuracy"] + ABILITY_KEYS + ["high_confidence_wrong_count"]
    lines = [
        "# Model Ability Run Comparison",
        "",
        f"Left: `{args.left_label}` from `{rel(left_path)}`",
        f"Right: `{args.right_label}` from `{rel(right_path)}`",
        "",
        "| Metric | Left | Right |",
        "|---|---:|---:|",
    ]
    for key in keys:
        lines.append(f"| {key} | {left.get(key)} | {right.get(key)} |")
    lines.extend([
        "",
        "Interpretation guide:",
        "",
        "- If strict/schema improves while ability metrics do not, the change is mainly format or grounding repair.",
        "- If raw-balanced changes ability metrics sharply, the model is sensitive to observation representation.",
        "- If real-service preservation falls, the prompt or evidence mode is over-inducing suspicion.",
    ])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
