"""Inspect task definitions for HoneyAgentBench."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from inspect_ai import Task, task

from honeyagentbench.constants import DEFAULT_SYSTEM_MESSAGE
from honeyagentbench.scorers import honey_deception_scorer
from honeyagentbench.tools import restricted_tools


def _as_name_filter(value: str | list[str] | tuple[str, ...] | None) -> set[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return {item.strip() for item in value.split(",") if item.strip()}
    return {str(item) for item in value}


def _fallback_dataset(root_dir: str, eval_names: set[str] | None, variant_names: set[str] | None):
    try:
        from inspect_ai.dataset import Sample
    except Exception as exc:  # pragma: no cover - requires inspect runtime
        raise RuntimeError("inspect-ai is required to build the fallback dataset") from exc

    samples = []
    root = Path(root_dir)
    for eval_file in sorted(root.glob("*/eval.yaml")):
        data = yaml.safe_load(eval_file.read_text(encoding="utf-8"))
        eval_name = data["name"]
        if eval_names and eval_name not in eval_names and eval_file.parent.name not in eval_names:
            continue
        for variant_name, variant in data.get("variants", {}).items():
            if variant_names and variant_name not in variant_names:
                continue
            samples.append(
                Sample(
                    input=f"{DEFAULT_SYSTEM_MESSAGE}\n\n{variant['prompt']}",
                    target="Submit a final report based only on restricted tool observations.",
                    metadata={
                        "eval_name": eval_name,
                        "variant_name": variant_name,
                        **data.get("metadata", {}),
                    },
                    sandbox=data.get("sandbox"),
                    files=data.get("files"),
                )
            )
    return samples


def _load_dataset(root_dir: str, eval_names: set[str] | None, variant_names: set[str] | None):
    root_path = Path(root_dir)
    if not root_path.is_absolute():
        root_path = Path(__file__).resolve().parents[1] / root_path
    resolved_root = str(root_path.resolve())
    try:
        from inspect_cyber import create_agentic_eval_dataset
    except Exception:
        return _fallback_dataset(root_dir, eval_names, variant_names)

    dataset = create_agentic_eval_dataset(root_dir=resolved_root)
    if not eval_names and not variant_names:
        return dataset
    return [
        sample
        for sample in dataset
        if (not eval_names or sample.metadata.get("eval_name") in eval_names)
        and (not variant_names or sample.metadata.get("variant_name") in variant_names)
    ]


def _environment_aware_solver():
    try:
        from inspect_ai.agent import as_solver, react
        from inspect_ai.solver import solver
    except Exception as exc:  # pragma: no cover - requires inspect runtime
        raise RuntimeError("inspect-ai is required to construct honeyagent_pilot") from exc

    solvers = {
        "ssh_like": as_solver(
            react(
                name="honeyagentbench_ssh_react",
                prompt=DEFAULT_SYSTEM_MESSAGE,
                tools=restricted_tools("ssh_like"),
            )
        ),
        "web": as_solver(
            react(
                name="honeyagentbench_web_react",
                prompt=DEFAULT_SYSTEM_MESSAGE,
                tools=restricted_tools("web"),
            )
        ),
        "multi_node": as_solver(
            react(
                name="honeyagentbench_multinode_react",
                prompt=DEFAULT_SYSTEM_MESSAGE,
                tools=restricted_tools("multi_node"),
            )
        ),
        "default": as_solver(
            react(
                name="honeyagentbench_react",
                prompt=DEFAULT_SYSTEM_MESSAGE,
                tools=restricted_tools(),
            )
        ),
    }

    @solver
    def honeyagent_environment_solver():
        async def solve(state, generate):
            environment_type = (state.metadata or {}).get("environment_type")
            selected_solver = solvers.get(environment_type, solvers["default"])
            return await selected_solver(state, generate)

        return solve

    return honeyagent_environment_solver()


@task
def honeyagent_pilot(root_dir: str = "evals", eval_names: str | list[str] | None = None, variant_names: str | list[str] | None = None):
    eval_filter = _as_name_filter(eval_names)
    variant_filter = _as_name_filter(variant_names)

    return Task(
        dataset=_load_dataset(root_dir, eval_filter, variant_filter),
        solver=_environment_aware_solver(),
        scorer=honey_deception_scorer(),
    )
