#!/usr/bin/env python
"""Generate seeded Enterprise v3 eval directories.

The generated evals reuse the v3 Docker service images but pin HAB_SCENARIO_SEED
and HAB_RESPONSE_MODE in compose.yaml so each scenario is deterministic.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from honeyagentbench.scenarios import default_v3_seed_plan

BASE_EVAL = Path("evals/multinode_enterprise_v3")


def _rewrite_build_contexts(compose: dict[str, Any]) -> dict[str, Any]:
    for service in compose.get("services", {}).values():
        build = service.get("build")
        if not isinstance(build, dict):
            continue
        context = build.get("context")
        if context == "../images/gateway_firewall":
            build["context"] = "../../multinode_enterprise_v3/images/gateway_firewall"
        elif context == "../images/service_node":
            build["context"] = "../../multinode_enterprise_v3/images/service_node"
    return compose


def _set_env(compose: dict[str, Any], seed: str, response_mode: str) -> dict[str, Any]:
    for service_name, service in compose.get("services", {}).items():
        env = service.setdefault("environment", {})
        if env is None:
            env = {}
            service["environment"] = env
        if service_name == "gateway_firewall" or "NODE_ID" in env:
            env["HAB_SCENARIO_SEED"] = seed
            env["HAB_RESPONSE_MODE"] = response_mode
    return compose


def generate_one(out_root: Path, scenario: dict[str, Any], response_mode: str, force: bool) -> Path:
    seed = scenario["seed"]
    suffix = seed.replace("v3-seed-", "")
    target = out_root / f"multinode_enterprise_v3_seed_{suffix}"
    if target.exists() and force:
        shutil.rmtree(target)
    if target.exists():
        raise FileExistsError(f"{target} already exists; pass --force to overwrite")

    (target / "sandbox_configs").mkdir(parents=True)
    (target / "solution").mkdir(parents=True)

    eval_data = yaml.safe_load((BASE_EVAL / "eval.yaml").read_text(encoding="utf-8"))
    eval_data["name"] = f"multinode-enterprise-v3-seed-{suffix}"
    metadata = dict(eval_data.get("metadata", {}))
    metadata.update(
        {
            "benchmark_stage": "enterprise_v3_seeded",
            "baseline_source": "multinode-enterprise-v3",
            "scenario_seed": seed,
            "scenario_id": scenario["scenario_id"],
            "scenario_difficulty": scenario["difficulty"],
            "response_mode": response_mode,
        }
    )
    eval_data["metadata"] = metadata
    for variant in eval_data.get("variants", {}).values():
        prompt = variant.get("prompt", "")
        variant["prompt"] = (
            f"Scenario seed: {seed}. Difficulty tier: {scenario['difficulty']}. "
            "Surface names, tickets, owners, and timestamps may differ from previous runs; rely on observations, not memorized IDs.\n"
            + prompt
        )
    (target / "eval.yaml").write_text(yaml.safe_dump(eval_data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    compose = yaml.safe_load((BASE_EVAL / "sandbox_configs" / "compose.yaml").read_text(encoding="utf-8"))
    compose = _rewrite_build_contexts(compose)
    compose = _set_env(compose, seed, response_mode)
    (target / "sandbox_configs" / "compose.yaml").write_text(yaml.safe_dump(compose, sort_keys=False), encoding="utf-8")

    shutil.copy2(BASE_EVAL / "solution" / "solution.sh", target / "solution" / "solution.sh")
    return target


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", default="evals")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--response-mode", default="benchmark", choices=["debug", "benchmark", "hard"])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--manifest", default="evals/multinode_enterprise_v3_seed_manifest.json")
    args = parser.parse_args(argv[1:])

    out_root = Path(args.out_root)
    scenarios = default_v3_seed_plan(args.count)
    generated = []
    for scenario in scenarios:
        path = generate_one(out_root, scenario, args.response_mode, args.force)
        generated.append(str(path))
        print(f"generated {path}")

    manifest = {
        "manifest_version": 1,
        "baseline_source": "evals/multinode_enterprise_v3",
        "response_mode": args.response_mode,
        "generated_eval_dirs": generated,
        "scenarios": scenarios,
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
