#!/usr/bin/env python3
"""Bootstrap a local HFish Client package for the realism-v1 Docker lab.

This script intentionally keeps HFish cookies, package URLs, node IDs, and
client package contents out of committed artifacts. The generated client.tgz is
written under runtime/, which is gitignored by this experiment directory.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILES = [
    ROOT / "configs" / "compose.realism-v1.yaml",
    ROOT / "configs" / "compose.realism-v1.pinned.yaml",
]
HFISH_SERVER_CONTAINER = "realism-control-hfish-server"
COOKIE_PATH = "/tmp/hfish_bootstrap_cookies.txt"
CONTROL_BASE = "https://127.0.0.1:4433"
DEFAULT_NODE_ADDR = "https://172.31.0.10:4434"
RUNTIME_PACKAGE = ROOT / "runtime" / "hfish" / "client.tgz"
ARTIFACT_DIR = ROOT / "artifacts" / "docker_inspect"


class BootstrapError(RuntimeError):
    pass


def run(cmd: list[str], *, input_bytes: bytes | None = None, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        stderr = proc.stderr.decode(errors="ignore").strip()
        stdout = proc.stdout.decode(errors="ignore").strip()
        raise BootstrapError(f"command failed ({proc.returncode}): {' '.join(cmd)}\nstdout={stdout[:500]}\nstderr={stderr[:500]}")
    return proc


def compose_cmd(*args: str) -> list[str]:
    cmd = ["docker", "compose"]
    for compose_file in COMPOSE_FILES:
        cmd.extend(["-f", str(compose_file.relative_to(ROOT))])
    cmd.extend(args)
    return cmd


def docker_exec_curl(args: list[str], *, payload: dict | None = None, timeout: int = 30) -> bytes:
    cmd = ["docker", "exec", "-i", HFISH_SERVER_CONTAINER, "curl", "-ksS", *args]
    input_bytes = None if payload is None else json.dumps(payload).encode("utf-8")
    proc = run(cmd, input_bytes=input_bytes, timeout=timeout)
    return proc.stdout


def parse_json(raw: bytes, context: str) -> dict:
    text = raw.decode("utf-8", errors="ignore")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise BootstrapError(f"{context} returned non-JSON response: {text[:200]!r}") from exc


def ensure_hfish_server_running(start: bool) -> None:
    inspect = run(
        ["docker", "inspect", "-f", "{{.State.Running}}", HFISH_SERVER_CONTAINER],
        check=False,
        timeout=10,
    )
    if inspect.returncode == 0 and inspect.stdout.decode().strip() == "true":
        return
    if not start:
        raise BootstrapError(f"{HFISH_SERVER_CONTAINER} is not running; rerun with --start-server or start hfish_server first")
    run(compose_cmd("up", "-d", "--pull", "never", "hfish_server"), timeout=60)
    deadline = time.time() + 60
    last_error = ""
    while time.time() < deadline:
        probe = run(
            [
                "docker",
                "exec",
                HFISH_SERVER_CONTAINER,
                "curl",
                "-ksS",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                f"{CONTROL_BASE}/web/login",
            ],
            check=False,
            timeout=10,
        )
        code = probe.stdout.decode(errors="ignore").strip()
        if probe.returncode == 0 and code == "200":
            return
        last_error = probe.stderr.decode(errors="ignore")[:200]
        time.sleep(2)
    raise BootstrapError(f"HFish server did not become ready within 60s: {last_error}")


def write_captcha() -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    raw = docker_exec_curl(["-c", COOKIE_PATH, "--max-time", "8", f"{CONTROL_BASE}/v1/captcha"])
    data = parse_json(raw, "captcha")
    if data.get("response_code") != 0:
        raise BootstrapError(f"captcha request failed: response_code={data.get('response_code')} verbose={data.get('verbose_msg')}")
    image_data = data.get("data", "")
    if "," not in image_data:
        raise BootstrapError("captcha response did not contain a data URI")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ARTIFACT_DIR / f"hfish_bootstrap_captcha_{stamp}.png"
    out.write_bytes(base64.b64decode(image_data.split(",", 1)[1]))
    latest = ARTIFACT_DIR / "hfish_bootstrap_captcha_latest.png"
    latest.write_bytes(out.read_bytes())
    return out


def login(captcha: str, username: str) -> int:
    password = os.environ.get("HFISH_ADMIN_PASSWORD")
    if not password:
        raise BootstrapError("HFISH_ADMIN_PASSWORD must be set when --captcha is provided")
    payload = {"username": username, "password": password, "captcha": captcha}
    raw = docker_exec_curl(
        [
            "-b",
            COOKIE_PATH,
            "-c",
            COOKIE_PATH,
            "-H",
            "Content-Type: application/json",
            "--data",
            "@-",
            f"{CONTROL_BASE}/v1/login",
        ],
        payload=payload,
    )
    data = parse_json(raw, "login")
    code = data.get("response_code")
    if code not in (0, 1039):
        raise BootstrapError(f"login failed: response_code={code} verbose={data.get('verbose_msg')}")
    return int(code)


def create_node_package(node_arch: str, node_addr: str) -> str:
    payload = {
        "node_arch": node_arch,
        "node_addr": node_addr,
        "location": "",
        "mould_id": "",
    }
    raw = docker_exec_curl(
        [
            "-b",
            COOKIE_PATH,
            "-H",
            "Content-Type: application/json",
            "--data",
            "@-",
            f"{CONTROL_BASE}/v1/node",
        ],
        payload=payload,
        timeout=45,
    )
    data = parse_json(raw, "node package generation")
    if data.get("response_code") != 0:
        raise BootstrapError(f"node package generation failed: response_code={data.get('response_code')} verbose={data.get('verbose_msg')}")
    package_url = (data.get("data") or {}).get("package")
    if not package_url:
        raise BootstrapError("node package generation succeeded but no package URL was returned")
    return package_url


def download_package(package_url: str) -> bytes:
    raw = docker_exec_curl(["-b", COOKIE_PATH, "--max-time", "20", package_url], timeout=30)
    if len(raw) < 128:
        preview = raw.decode("utf-8", errors="ignore")[:120]
        raise BootstrapError(f"downloaded package is too small ({len(raw)} bytes): {preview!r}")
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
            names = tf.getnames()
    except tarfile.TarError as exc:
        preview = raw[:80].hex()
        raise BootstrapError(f"downloaded package is not a valid gzip tarball; first bytes={preview}") from exc
    if "client" not in {Path(name).name for name in names}:
        raise BootstrapError(f"downloaded package does not contain a client binary; members={names}")
    return raw


def write_package(raw: bytes, package_url: str, login_code: int, node_arch: str, node_addr: str) -> Path:
    RUNTIME_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_PACKAGE.write_bytes(raw)
    RUNTIME_PACKAGE.chmod(0o644)
    digest = hashlib.sha256(raw).hexdigest()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
        members = sorted(tf.getnames())
    split = urlsplit(package_url)
    summary = {
        "schema_version": "hfish-client-bootstrap-v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "login_response_code": login_code,
        "node_arch": node_arch,
        "node_addr": node_addr,
        "package_url_host": split.hostname,
        "package_url_port": split.port,
        "package_url_path_redacted": "/v1/node/[REDACTED]",
        "package_path": str(RUNTIME_PACKAGE.relative_to(ROOT)),
        "package_bytes": len(raw),
        "package_sha256": digest,
        "tar_members": members,
        "secret_handling": "cookie, package URL, node ID, and package contents are not stored in committed artifacts",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = ARTIFACT_DIR / "hfish_client_bootstrap_summary_latest.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    dated = ARTIFACT_DIR / f"hfish_client_bootstrap_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    dated.write_text(summary_path.read_text(encoding="utf-8"), encoding="utf-8")
    return summary_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a local HFish client.tgz for Docker Client bootstrap")
    parser.add_argument("--start-server", action="store_true", help="Start hfish_server with docker compose --pull never when it is not running")
    parser.add_argument("--captcha", help="Captcha text from the generated captcha image")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--node-arch", default="linux-386")
    parser.add_argument("--node-addr", default=DEFAULT_NODE_ADDR)
    args = parser.parse_args()

    try:
        ensure_hfish_server_running(args.start_server)
        if not args.captcha:
            captcha_path = write_captcha()
            print(f"captcha_image={captcha_path}")
            print("Set HFISH_ADMIN_PASSWORD and rerun with --captcha <text> to generate runtime/hfish/client.tgz.")
            return 0
        login_code = login(args.captcha, args.username)
        package_url = create_node_package(args.node_arch, args.node_addr)
        raw = download_package(package_url)
        summary_path = write_package(raw, package_url, login_code, args.node_arch, args.node_addr)
        print(f"package_path={RUNTIME_PACKAGE}")
        print(f"summary={summary_path}")
        print("HFish client package bootstrap complete")
        return 0
    except BootstrapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
