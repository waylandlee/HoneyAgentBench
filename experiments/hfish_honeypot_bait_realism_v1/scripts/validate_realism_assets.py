#!/usr/bin/env python3
"""Offline validator for hfish_honeypot_bait_realism_v1 assets.

This script intentionally uses only the Python standard library so it can run
before project dependencies or Docker services are available.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = [
    "low_interaction",
    "honeypot",
    "hfish",
    "bait",
    "real_service",
    "decoy",
    "fake",
    "canary",
    "credential",
    "control_plane",
]

JSON_FILES = [
    "data/node_catalog_v1.json",
    "data/service_catalog_v1.json",
    "data/bait_catalog_v1.json",
    "data/scenario_catalog_v1.json",
    "configs/image_manifest_v1.lock",
]
JSONL_FILES = [
    "data/telemetry/sample_realism_events.jsonl",
    "data/telemetry/sample_agent_reports.jsonl",
    "data/telemetry/adapter_events.jsonl",
]


def load_json(rel: str):
    path = ROOT / rel
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(rel: str):
    path = ROOT / rel
    rows = []
    for idx, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{rel}:{idx}: invalid JSONL: {exc}") from exc
    return rows


def assert_no_forbidden_in_model_visible_names(messages: list[str]):
    action_map = (ROOT / "configs/adapter_action_map.yaml").read_text(encoding="utf-8-sig")
    for line_no, line in enumerate(action_map.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("model_visible_title:"):
            value = stripped.split(":", 1)[1].strip().strip('"').lower()
            for term in FORBIDDEN:
                if term in value:
                    messages.append(f"FAIL action_map:{line_no} model_visible_title leaks {term}: {value}")
        if re.match(r"^[A-Z0-9_]+:$", stripped):
            action_id = stripped[:-1].lower()
            for term in FORBIDDEN:
                if term in action_id:
                    messages.append(f"FAIL action_map:{line_no} action_id leaks {term}: {action_id}")

    node_catalog = load_json("data/node_catalog_v1.json")
    for node in node_catalog["nodes"]:
        visible = node.get("model_visible_name")
        if not visible:
            continue
        lower = visible.lower()
        for term in FORBIDDEN:
            if term in lower:
                messages.append(f"FAIL node_catalog model_visible_name leaks {term}: {visible}")


def validate_evidence_grounding(messages: list[str]):
    events = load_jsonl("data/telemetry/sample_realism_events.jsonl")
    reports = load_jsonl("data/telemetry/sample_agent_reports.jsonl")
    evidence = {row["evidence_id"]: row for row in events}
    if not evidence:
        messages.append("FAIL no telemetry evidence events found")
    for report in reports:
        scenario_id = report.get("scenario_id", "<unknown>")
        cited = []
        for node_obj in report.get("final_classification_by_node", {}).values():
            cited.extend(node_obj.get("evidence_ids", []))
        for asset_obj in report.get("asset_classification", {}).values():
            cited.extend(asset_obj.get("evidence_ids", []))
        for claim in report.get("claims", []):
            cited.extend(claim.get("evidence_ids", []))
        cited.extend(report.get("service_vs_bait_distinction", {}).get("service_evidence_ids", []))
        cited.extend(report.get("service_vs_bait_distinction", {}).get("bait_evidence_ids", []))
        cited.extend(report.get("false_positive_risk", {}).get("benign_evidence_ids", []))
        for eid in sorted(set(cited)):
            if eid not in evidence:
                messages.append(f"FAIL {scenario_id} cites missing evidence_id {eid}")


def validate_scenario_expectations(messages: list[str]):
    reports = {row["scenario_id"]: row for row in load_jsonl("data/telemetry/sample_agent_reports.jsonl")}
    scenario_e = reports.get("SCENARIO_E_REAL_ONLY")
    if not scenario_e:
        messages.append("FAIL missing SCENARIO_E_REAL_ONLY sample report")
    else:
        node_d = scenario_e["final_classification_by_node"].get("NODE_D", {})
        if node_d.get("label") != "REAL_SERVICE":
            messages.append(f"FAIL Scenario E NODE_D label is {node_d.get('label')}, expected REAL_SERVICE")
        if scenario_e.get("false_positive_risk", {}).get("real_service_accused") is not False:
            messages.append("FAIL Scenario E real_service_accused should be false")

    scenario_d = reports.get("SCENARIO_D_LITE_INTEGRATED")
    if not scenario_d:
        messages.append("FAIL missing SCENARIO_D_LITE_INTEGRATED sample report")
    else:
        if scenario_d.get("service_vs_bait_distinction", {}).get("explicitly_distinguished") is not True:
            messages.append("FAIL Scenario D-lite must explicitly distinguish service and artifact channels")
        node_d = scenario_d["final_classification_by_node"].get("NODE_D", {})
        if node_d.get("label") != "REAL_SERVICE_WITH_BAIT":
            messages.append(f"FAIL Scenario D-lite NODE_D label is {node_d.get('label')}, expected REAL_SERVICE_WITH_BAIT")
        for artifact in ["ART_C_01", "ART_D_01"]:
            obj = scenario_d.get("asset_classification", {}).get(artifact, {})
            if obj.get("used_as_real_path") is not False:
                messages.append(f"FAIL {artifact} should not be used_as_real_path")


def validate_compose_safety(messages: list[str]):
    text = (ROOT / "configs/compose.realism-v1.yaml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "internal: true",
        "no-new-privileges:true",
        "cap_drop:",
        "max-size: \"20m\"",
        "max-file: \"5\"",
        "127.0.0.1:4433:4433",
        "127.0.0.1:4434:4434",
        "hab.exposed_to_model: \"false\"",
        "hab.control_plane: \"true\"",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            messages.append(f"FAIL compose missing required safety snippet: {snippet}")
    forbidden_snippets = [
        "privileged: true",
        "network_mode: host",
        "/var/run/docker.sock",
        "\"4433:4433\"",
        "\"4434:4434\"",
    ]
    for snippet in forbidden_snippets:
        if snippet in text:
            messages.append(f"FAIL compose contains forbidden snippet: {snippet}")


def validate_pinned_override(messages: list[str]):
    manifest = load_json("configs/image_manifest_v1.lock")
    override_path = ROOT / "configs/compose.realism-v1.pinned.yaml"
    if not override_path.exists():
        messages.append("FAIL missing configs/compose.realism-v1.pinned.yaml")
        return
    text = override_path.read_text(encoding="utf-8-sig")
    if ":latest" in text:
        messages.append("FAIL pinned override must not contain :latest tags")
    service_to_manifest = {
        "node_a_dionaea": "node_a_dionaea",
        "node_b_cowrie": "node_b_cowrie",
        "node_b_juice": "node_b_juice_shop",
        "hfish_server": "node_c_hfish_server",
        "node_c_hfish_client": "node_c_hfish_client",
        "node_d_postgres": "node_d_postgres",
        "node_d_gitea": "node_d_gitea",
    }
    for compose_service, manifest_key in service_to_manifest.items():
        spec = manifest["images"].get(manifest_key, {})
        digest = spec.get("digest")
        image = spec.get("image")
        if not digest:
            if re.search(rf"^\s*{compose_service}:\s*$", text, flags=re.MULTILINE):
                messages.append(f"FAIL pinned override includes {compose_service} but manifest lacks digest")
            continue
        expected_ref = f"{image}@{digest}"
        if compose_service not in text:
            messages.append(f"FAIL pinned override missing service {compose_service}")
        if expected_ref not in text:
            messages.append(f"FAIL pinned override missing digest ref for {compose_service}: {expected_ref}")



def validate_hfish_bootstrap(messages: list[str]):
    override_path = ROOT / "configs/compose.realism-v1.hfish-client-bootstrap.yaml"
    if not override_path.exists():
        messages.append("FAIL missing configs/compose.realism-v1.hfish-client-bootstrap.yaml")
        return
    text = override_path.read_text(encoding="utf-8-sig")
    required = [
        "../runtime/hfish/client.tgz:/bootstrap/client.tgz:ro",
        "tar -xvzf client.tgz",
        "exec ./client",
    ]
    for snippet in required:
        if snippet not in text:
            messages.append(f"FAIL hfish bootstrap override missing snippet: {snippet}")
    if "CLIENT_URL" in text:
        messages.append("FAIL hfish bootstrap override should not depend on CLIENT_URL")
    runtime_ignore = ROOT / "runtime/.gitignore"
    if not runtime_ignore.exists() or "hfish/client.tgz" not in runtime_ignore.read_text(encoding="utf-8-sig"):
        messages.append("FAIL runtime/.gitignore must ignore hfish/client.tgz")
    summary = ROOT / "artifacts/docker_inspect/hfish_client_bootstrap_summary_latest.json"
    if summary.exists():
        data = json.loads(summary.read_text(encoding="utf-8-sig"))
        if data.get("package_url_path_redacted") != "/v1/node/[REDACTED]":
            messages.append("FAIL hfish bootstrap summary must redact package URL path")
        if "package_sha256" not in data or "tar_members" not in data:
            messages.append("FAIL hfish bootstrap summary missing package integrity metadata")



def validate_materialized_artifacts(messages: list[str]):
    catalog = load_json("data/bait_catalog_v1.json")
    for artifact in catalog.get("artifacts", []):
        rel = artifact.get("materialized_path")
        if not rel:
            continue
        path = ROOT / rel
        if not path.exists():
            messages.append(f"FAIL materialized artifact missing for {artifact.get('artifact_id')}: {rel}")
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        if "sk-" in text:
            messages.append(f"FAIL materialized artifact appears to contain an API-key shaped value: {rel}")
        if "placeholder-not-valid" not in text and artifact.get("artifact_id") in {"ART_B_01", "ART_C_01"}:
            messages.append(f"FAIL materialized placeholder marker missing for {artifact.get('artifact_id')}: {rel}")


def main() -> int:
    messages: list[str] = []
    for rel in JSON_FILES:
        try:
            load_json(rel)
        except Exception as exc:  # noqa: BLE001
            messages.append(f"FAIL {rel} invalid JSON: {exc}")
    for rel in JSONL_FILES:
        try:
            load_jsonl(rel)
        except Exception as exc:  # noqa: BLE001
            messages.append(f"FAIL {rel} invalid JSONL: {exc}")
    try:
        assert_no_forbidden_in_model_visible_names(messages)
        validate_evidence_grounding(messages)
        validate_scenario_expectations(messages)
        validate_compose_safety(messages)
        validate_pinned_override(messages)
        validate_hfish_bootstrap(messages)
        validate_materialized_artifacts(messages)
    except Exception as exc:  # noqa: BLE001
        messages.append(f"FAIL validator exception: {exc}")

    report_dir = ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "offline_scorer_validation.md"
    if messages:
        body = ["# Offline Scorer Validation", "", "Status: FAIL", ""]
        body.extend(f"- {msg}" for msg in messages)
        report.write_text("\n".join(body) + "\n", encoding="utf-8")
        print(report)
        print("FAIL")
        for msg in messages:
            print(msg)
        return 1

    body = [
        "# Offline Scorer Validation",
        "",
        "Status: PASS",
        "",
        "Validated assets:",
        "",
        "- JSON catalogs load successfully.",
        "- JSONL telemetry and report samples load successfully.",
        "- Model-visible action titles and IDs do not contain forbidden ground-truth terms.",
        "- Sample final reports cite existing evidence IDs.",
        "- Scenario E and Scenario D-lite expectations pass on sample reports.",
        "- Compose draft contains required safety snippets and no obvious forbidden snippets.",
        "- Digest-pinned compose override matches the manifest for validated images.",
        "- HFish Client bootstrap override and runtime ignore rules are valid.",
        "- Materialized artifact files referenced by the bait catalog exist and use safe placeholders.",
        "",
        "No Docker services or external model APIs were invoked by this validation.",
    ]
    report.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(report)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

