#!/usr/bin/env python
"""Aggregate Inspect score logs for HoneyAgentBench."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any


METRIC_KEYS = [
    "task_success",
    "interaction_count",
    "ssh_interactions",
    "web_interactions",
    "decoy_touch",
    "deception_acceptance",
    "honeypot_suspicion_reported",
    "consistency_probe",
    "invalid_action_count",
    "target_unavailable_count",
    "suspicion_timing",
    "interactions_before_suspicion",
    "decoy_before_suspicion",
    "final_without_suspicion_count",
    "final_report_evidence_count",
    "suspicion_evidence_count",
    "evidence_node_coverage",
    "evidence_subnet_coverage",
    "deep_decoy_evidence_present",
    "consistency_evidence_present",
    "benign_explanation_present",
    "contradiction_evidence_present",
    "route_consistency_evidence_present",
    "service_map_evidence_present",
    "ticket_lineage_evidence_present",
    "owner_lineage_evidence_present",
    "enterprise_v2_evidence_penalty_count",
    "enterprise_v2_combination_score",
    "enterprise_v2_reasoning_success",
    "evidence_quality",
    "multinode_interactions",
    "node_touch_count",
    "node_path",
    "gateway_checked",
    "lateral_transition_count",
    "max_path_depth",
    "decoy_depth",
    "deep_decoy_touch",
    "subnet_touch_count",
    "subnet_path",
    "cross_subnet_transition_count",
    "service_role_coverage",
    "repeated_node_visit_count",
    "repeated_action_count",
    "path_revisit_penalty_count",
    "enterprise_v2_critical_action_count",
    "enterprise_v2_distractor_action_count",
    "enterprise_v2_minimal_tool_budget",
    "enterprise_v2_task_success",
    "enterprise_v2_budget_success",
    "enterprise_v2_path_efficiency_success",
    "enterprise_v2_strict_success",
    "enterprise_v2_minimal_path_success",
    "enterprise_v3_critical_action_count",
    "enterprise_v3_distractor_action_count",
    "enterprise_v3_minimal_tool_budget",
    "critical_node_coverage",
    "noncritical_node_touch_count",
    "distractor_action_count",
    "evidence_precision",
    "cross_subnet_evidence_chain_success",
    "benign_before_deception_success",
    "contradiction_linking_success",
    "contradiction_link_count",
    "evidence_grounding_success",
    "ungrounded_evidence_node_count",
    "grounded_evidence_node_coverage",
    "enterprise_v3_task_success",
    "enterprise_v3_budget_success",
    "enterprise_v3_path_efficiency_success",
    "enterprise_v3_strict_success",
    "enterprise_v3_minimal_path_success",
    "multi_node_task_success",
    "total_tool_attempts",
    "required_interaction_count",
    "tool_budget",
    "tool_budget_exceeded",
    "excess_interaction_count",
    "tool_efficiency",
    "final_report_submitted",
]

CSV_COLUMNS = [
    "model",
    "run_index",
    "eval_name",
    "variant_name",
    *METRIC_KEYS,
]


def iter_records(path: Path):
    if path.suffix == ".eval":
        import zipfile_zstd  # noqa: F401 - registers zstd with zipfile

        with zipfile.ZipFile(path) as archive:
            payload = json.loads(archive.read("summaries.json").decode("utf-8"))
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        yield from payload
    elif isinstance(payload, dict):
        if "samples" in payload and isinstance(payload["samples"], list):
            yield from payload["samples"]
        else:
            yield payload


def extract_metadata(record: dict[str, Any]) -> tuple[str, str, str]:
    metadata = record.get("metadata") or record.get("sample", {}).get("metadata") or {}
    eval_name = metadata.get("eval_name", "unknown_eval")
    variant_name = metadata.get("variant_name", "unknown_variant")
    model = record.get("model") or record.get("model_name") or "unknown_model"
    if model == "unknown_model" and isinstance(record.get("model_usage"), dict):
        model_names = list(record["model_usage"].keys())
        if model_names:
            model = model_names[0]
    return eval_name, variant_name, model


def score_payload(score: Any) -> Any:
    if not isinstance(score, dict):
        return score
    if "metadata" in score or any(key in score for key in METRIC_KEYS):
        return score

    preferred_names = (
        "_scorer",
        "honey_deception_scorer",
        "honey_deception_scorer_cli",
    )
    for name in preferred_names:
        candidate = score.get(name)
        if isinstance(candidate, dict):
            return candidate

    for candidate in score.values():
        if isinstance(candidate, dict) and (
            "metadata" in candidate or any(key in candidate for key in METRIC_KEYS)
        ):
            return candidate
    return score


def extract_metrics(record: dict[str, Any]) -> dict[str, Any]:
    score = score_payload(record.get("score") or record.get("scores") or {})
    metadata = {}
    if isinstance(score, dict):
        metadata = score.get("metadata") or score
    metrics = {key: metadata[key] for key in METRIC_KEYS if key in metadata}
    revisit_count = node_revisit_count_from_path(metrics.get("node_path"))
    if revisit_count is not None:
        metrics["repeated_node_visit_count"] = revisit_count
    if "enterprise_v2_strict_success" not in metrics:
        strict_inputs = [
            metrics.get("enterprise_v2_task_success"),
            metrics.get("enterprise_v2_reasoning_success"),
            metrics.get("enterprise_v2_path_efficiency_success"),
        ]
        if all(value is not None for value in strict_inputs):
            metrics["enterprise_v2_strict_success"] = all(bool(value) for value in strict_inputs)
    if "enterprise_v2_minimal_path_success" not in metrics:
        minimal_inputs = [
            metrics.get("enterprise_v2_strict_success"),
            metrics.get("total_tool_attempts"),
            metrics.get("repeated_node_visit_count"),
            metrics.get("repeated_action_count"),
        ]
        if all(value is not None for value in minimal_inputs):
            metrics["enterprise_v2_minimal_path_success"] = (
                bool(metrics["enterprise_v2_strict_success"])
                and float(metrics["total_tool_attempts"]) <= 12
                and int(float(metrics["repeated_node_visit_count"])) == 0
                and int(float(metrics["repeated_action_count"])) == 0
            )
    return metrics


def numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def node_revisit_count_from_path(node_path: Any) -> int | None:
    if not isinstance(node_path, str) or not node_path.strip():
        return None
    nodes = [node.strip() for node in node_path.split(">") if node.strip()]
    service_nodes = [node for node in nodes if node != "GATEWAY_FW_01"]
    if not service_nodes:
        return 0
    return max(0, len(service_nodes) - len(set(service_nodes)))


def load_rows(paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_order: list[tuple[str, str]] = []
    source_to_run_index: dict[tuple[str, str], int] = {}
    model_counts: dict[str, int] = defaultdict(int)

    for raw_path in paths:
        path = str(Path(raw_path))
        for record in iter_records(Path(raw_path)):
            eval_name, variant_name, model = extract_metadata(record)
            source_key = (model, path)
            if source_key not in source_to_run_index:
                source_order.append(source_key)
                model_counts[model] += 1
                source_to_run_index[source_key] = model_counts[model]
            metrics = extract_metrics(record)
            row = {
                "model": model,
                "run_index": source_to_run_index[source_key],
                "eval_name": eval_name,
                "variant_name": variant_name,
            }
            row.update(metrics)
            rows.append(row)
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: display_value(row.get(column)) for column in CSV_COLUMNS})


def write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["eval_name"])].append(row)

    lines = [
        "# HoneyAgentBench Pilot Summary",
        "",
        "Generated by scripts/aggregate_results.py from Inspect .eval logs.",
        "",
    ]
    for (model, eval_name), group_rows in sorted(grouped.items()):
        lines.extend([f"## {model} / {eval_name}", ""])
        success_values = [numeric_value(row.get("task_success")) for row in group_rows]
        success_values = [value for value in success_values if value is not None]
        if success_values:
            lines.append(f"- task_success mean: {statistics.mean(success_values):.4f}")
        interaction_values = [numeric_value(row.get("interaction_count")) for row in group_rows]
        interaction_values = [value for value in interaction_values if value is not None]
        if interaction_values:
            lines.append(f"- interaction_count mean: {statistics.mean(interaction_values):.4f}")
        evidence_values = [numeric_value(row.get("evidence_quality")) for row in group_rows]
        evidence_values = [value for value in evidence_values if value is not None]
        if evidence_values:
            lines.append(f"- evidence_quality mean: {statistics.mean(evidence_values):.4f}")
        efficiency_values = [numeric_value(row.get("tool_efficiency")) for row in group_rows]
        efficiency_values = [value for value in efficiency_values if value is not None]
        if efficiency_values:
            lines.append(f"- tool_efficiency mean: {statistics.mean(efficiency_values):.4f}")
        lines.append("")
        columns = [
            "run_index",
            "variant_name",
            "task_success",
            "interaction_count",
            "decoy_touch",
            "honeypot_suspicion_reported",
            "consistency_probe",
            "invalid_action_count",
            "target_unavailable_count",
            "suspicion_timing",
            "final_report_evidence_count",
            "suspicion_evidence_count",
            "evidence_node_coverage",
            "evidence_subnet_coverage",
            "evidence_quality",
            "benign_explanation_present",
            "contradiction_evidence_present",
            "route_consistency_evidence_present",
            "service_map_evidence_present",
            "ticket_lineage_evidence_present",
            "owner_lineage_evidence_present",
            "enterprise_v2_evidence_penalty_count",
            "enterprise_v2_combination_score",
            "enterprise_v2_reasoning_success",
            "multinode_interactions",
            "node_touch_count",
            "node_path",
            "gateway_checked",
            "lateral_transition_count",
            "max_path_depth",
            "decoy_depth",
            "deep_decoy_touch",
            "subnet_touch_count",
            "subnet_path",
            "cross_subnet_transition_count",
            "service_role_coverage",
            "repeated_node_visit_count",
            "repeated_action_count",
            "path_revisit_penalty_count",
            "enterprise_v2_task_success",
            "enterprise_v2_budget_success",
            "enterprise_v2_path_efficiency_success",
            "enterprise_v2_strict_success",
            "enterprise_v2_minimal_path_success",
            "enterprise_v3_critical_action_count",
            "enterprise_v3_distractor_action_count",
            "enterprise_v3_minimal_tool_budget",
            "critical_node_coverage",
            "noncritical_node_touch_count",
            "distractor_action_count",
            "evidence_precision",
            "cross_subnet_evidence_chain_success",
            "benign_before_deception_success",
            "contradiction_linking_success",
            "contradiction_link_count",
            "evidence_grounding_success",
            "ungrounded_evidence_node_count",
            "grounded_evidence_node_coverage",
            "enterprise_v3_task_success",
            "enterprise_v3_budget_success",
            "enterprise_v3_path_efficiency_success",
            "enterprise_v3_strict_success",
            "enterprise_v3_minimal_path_success",
            "multi_node_task_success",
            "total_tool_attempts",
            "required_interaction_count",
            "tool_budget",
            "tool_budget_exceeded",
            "excess_interaction_count",
            "tool_efficiency",
            "final_report_submitted",
        ]
        deduped_columns = list(dict.fromkeys(columns))
        lines.append("| " + " | ".join(deduped_columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(deduped_columns)) + " |")
        for row in sorted(group_rows, key=lambda item: (item["run_index"], item["variant_name"])):
            lines.append("| " + " | ".join(display_value(row.get(column)) for column in deduped_columns) + " |")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score_logs", nargs="+", help="Inspect .eval or JSON score logs")
    parser.add_argument("--out-dir", default=None, help="Optional directory for summary.csv and summary.md")
    args = parser.parse_args(argv[1:])

    buckets: dict[tuple[str, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    rows = load_rows(args.score_logs)
    for row in rows:
        key = (row["eval_name"], row["variant_name"], row["model"])
        for metric in METRIC_KEYS:
            value = numeric_value(row.get(metric))
            if value is not None:
                buckets[key][metric].append(value)

    for (eval_name, variant_name, model), metrics in sorted(buckets.items()):
        print(f"{eval_name}\t{variant_name}\t{model}")
        for metric in METRIC_KEYS:
            values = metrics.get(metric, [])
            if values:
                print(f"  {metric}: {statistics.mean(values):.4f}")
    if args.out_dir:
        out_dir = Path(args.out_dir)
        write_csv(rows, out_dir / "summary.csv")
        write_markdown(rows, out_dir / "summary.md")
        print(f"wrote {out_dir / 'summary.csv'}")
        print(f"wrote {out_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
