#!/usr/bin/env python
"""Write a redacted, reproducible HoneyAgentBench run manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_info(raw_path: str) -> dict[str, Any]:
    path = Path(raw_path)
    return {
        "path": raw_path,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "sha256": sha256_file(path),
    }


def git_commit(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def redacted_env(keys: list[str]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for key in keys:
        value = os.environ.get(key)
        sensitive = any(marker in key.upper() for marker in SECRET_MARKERS)
        output[key] = {
            "present": value is not None,
            "value": "<redacted>" if value is not None and sensitive else value,
            "redacted": bool(value is not None and sensitive),
        }
    return output


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    cwd = Path(args.cwd).resolve()
    result_files = list(args.result_file or [])
    out_dir = Path(args.out_dir)
    for default_name in ("summary.csv", "summary.md"):
        candidate = out_dir / default_name
        if candidate.exists() and str(candidate) not in result_files:
            result_files.append(str(candidate))

    return {
        "manifest_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "HoneyAgentBench",
        "cwd": str(cwd),
        "git_commit": git_commit(cwd),
        "phase": args.phase,
        "run_name": args.run_name,
        "model": args.model,
        "eval_name": args.eval_name,
        "variant_name": args.variant_name,
        "scenario_seed": args.scenario_seed,
        "response_mode": args.response_mode,
        "command": args.command,
        "docker_image_tag": args.docker_image_tag,
        "score_logs": [path_info(path) for path in (args.score_log or [])],
        "result_files": [path_info(path) for path in result_files],
        "environment": redacted_env(args.env_key or []),
        "notes": args.note or [],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, help="Directory that will contain manifest.json")
    parser.add_argument("--cwd", default=".", help="Project working directory used for git metadata")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--phase", default="phase1-baseline")
    parser.add_argument("--model", default=None)
    parser.add_argument("--eval-name", default=None)
    parser.add_argument("--variant-name", default=None)
    parser.add_argument("--scenario-seed", default=None)
    parser.add_argument("--response-mode", default=None)
    parser.add_argument("--command", action="append", default=[])
    parser.add_argument("--score-log", action="append", default=[])
    parser.add_argument("--result-file", action="append", default=[])
    parser.add_argument("--env-key", action="append", default=[])
    parser.add_argument("--docker-image-tag", default=None)
    parser.add_argument("--note", action="append", default=[])
    args = parser.parse_args(argv[1:])

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(args)
    target = out_dir / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
