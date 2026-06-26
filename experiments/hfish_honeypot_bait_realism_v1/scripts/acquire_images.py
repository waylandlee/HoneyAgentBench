#!/usr/bin/env python3
"""Acquire Docker images for the realism benchmark with bounded pulls.

This script is intentionally small and dependency-free. It turns image acquisition
into an auditable gate: each service gets a bounded pull attempt, a digest check,
and a JSON result record.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "configs" / "image_manifest_v1.lock"
DEFAULT_OUTPUT = ROOT / "artifacts" / "docker_inspect" / "image_acquisition_latest.json"


def load_manifest() -> dict[str, Any]:
    with MANIFEST.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def image_ref(spec: dict[str, Any]) -> str | None:
    image = spec.get("image")
    tag = spec.get("tag")
    if not image or image == "local-build":
        return None
    if tag:
        return f"{image}:{tag}"
    return image


def run(cmd: list[str], timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)


def inspect_digest(ref: str) -> str | None:
    proc = run(["docker", "image", "inspect", ref, "--format", "{{json .RepoDigests}}"])
    if proc.returncode != 0:
        return None
    try:
        digests = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        return None
    if not digests:
        return None
    return digests[0]


def acquire(service: str, spec: dict[str, Any], timeout: int, dry_run: bool) -> dict[str, Any]:
    ref = image_ref(spec)
    now = datetime.now(timezone.utc).isoformat()
    result: dict[str, Any] = {
        "service": service,
        "image": ref,
        "started_at_utc": now,
        "dry_run": dry_run,
        "status": "skipped",
        "digest": None,
        "log_tail": "",
    }
    if ref is None:
        result["status"] = "skipped-local-build-or-missing-image"
        return result
    if dry_run:
        result["status"] = "dry-run"
        result["digest"] = inspect_digest(ref)
        return result
    try:
        proc = run(["docker", "pull", ref], timeout=timeout)
        result["returncode"] = proc.returncode
        result["log_tail"] = proc.stdout[-4000:]
        if proc.returncode == 0:
            result["status"] = "pass"
            result["digest"] = inspect_digest(ref)
        else:
            result["status"] = f"fail-{proc.returncode}"
            result["digest"] = inspect_digest(ref)
    except subprocess.TimeoutExpired as exc:
        result["status"] = "timeout"
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        result["log_tail"] = out[-4000:]
        result["digest"] = inspect_digest(ref)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire realism benchmark Docker images")
    parser.add_argument("--service", action="append", help="Service key from image_manifest_v1.lock; repeatable")
    parser.add_argument("--timeout", type=int, default=300, help="Per-image docker pull timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Do not pull; only show selected images and existing digests")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON output path")
    args = parser.parse_args()

    manifest = load_manifest()
    images = manifest.get("images", {})
    selected = args.service or list(images.keys())
    unknown = [name for name in selected if name not in images]
    if unknown:
        print(f"Unknown services: {', '.join(unknown)}", file=sys.stderr)
        return 2

    results = [acquire(name, images[name], args.timeout, args.dry_run) for name in selected]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "image-acquisition-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": args.timeout,
        "results": results,
    }
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)
    for item in results:
        print(f"{item['service']}\t{item['status']}\t{item.get('image') or 'NA'}\t{item.get('digest') or 'NA'}")
    if any(item["status"].startswith("fail") or item["status"] == "timeout" for item in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
