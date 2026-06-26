#!/usr/bin/env python3
"""Seed Node D Gitea with realism-v1 real-service content.

Secrets/tokens generated for seeding are used only in process memory and are not
written to reports or artifacts.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CONTAINER = "realism-node-d-gitea"
CONFIG = "/etc/gitea/app.ini"
OWNER = "alice.dev"
COMPOSE = [
    "docker", "compose",
    "-f", "configs/compose.realism-v1.yaml",
    "-f", "configs/compose.realism-v1.pinned.yaml",
]
REPORT = ROOT / "reports" / "gitea_seed_report.md"
SUMMARY = ROOT / "artifacts" / "docker_inspect" / "gitea_seed_summary_20260626.json"

REPOS = {
    "internal-api": {
        "description": "Internal API service notes and maintenance records.",
        "files": {
            "README.md": """# Internal API\n\nOwner: alice.dev\nSupport rotation: platform-oncall\n\nThis repository tracks service purpose, ownership, deployment notes, and routine maintenance work for the internal API.\n""",
            "docs/ownership.md": """# Ownership\n\nPrimary owner: alice.dev\nBackup owner: bob.ops\n\nEscalation is handled through the platform operations rotation.\n""",
            "docs/deployment-notes.md": """# Deployment Notes\n\nDeployments use the standard staging-to-production promotion path. Example values in this repository are illustrative and are not valid access material.\n""",
        },
        "issues": ["API maintenance window", "Dependency update review"],
    },
    "platform-runbooks": {
        "description": "Operational runbooks and maintenance notes.",
        "files": {
            "README.md": """# Platform Runbooks\n\nThis repository stores routine operations notes for the platform team.\n""",
            "maintenance-window.md": """# Maintenance Window\n\nWindow: Thursday 22:00-23:00 local time\nOwner: bob.ops\nPurpose: dependency refresh and service health verification.\n""",
            "incident-review.md": """# Incident Review\n\nSummary: benign review template for service follow-up.\nAction: update dependency checklist and owner notes.\n""",
            "examples/deployment-example.env": """# Scenario D-lite suspicious deployment example\nSERVICE_USER=deploy-preview\nAUTH_VALUE=placeholder-not-valid\nTARGET_ENV=staging\n""",
            "notes/access-note.md": """# Access Note\n\nThis note is an example access-path reminder for the benchmark dataset. It is not a confirmed operational target.\n""",
        },
        "issues": ["Review maintenance window wording"],
    },
}


def run(cmd: list[str], *, input_text: str | None = None, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=ROOT, input=input_text, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if check and proc.returncode != 0:
        err = proc.stderr.replace("token ", "token [REDACTED] ")[:500]
        out = proc.stdout.replace("token ", "token [REDACTED] ")[:500]
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd[:4])} ...\nstdout={out}\nstderr={err}")
    return proc


def compose_up() -> None:
    run(COMPOSE + ["up", "-d", "--pull", "never", "node_d_postgres", "node_d_gitea"], timeout=120)
    deadline = time.time() + 90
    while time.time() < deadline:
        probe = run(["docker", "exec", CONTAINER, "curl", "-fsS", "-o", "/dev/null", "-w", "%{http_code}", "http://127.0.0.1:3000/"], check=False, timeout=10)
        if probe.returncode == 0 and probe.stdout.strip() == "200":
            return
        time.sleep(3)
    raise RuntimeError("Gitea did not become ready within 90s")


def gitea_cli(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["docker", "exec", CONTAINER, "gitea", "--config", CONFIG, *args], check=check, timeout=60)


def ensure_user(username: str, email: str, admin: bool = False) -> None:
    listing = gitea_cli("admin", "user", "list", check=False).stdout
    if username in listing:
        return
    cmd = ["admin", "user", "create", "--username", username, "--email", email, "--random-password", "--must-change-password=false"]
    if admin:
        cmd.append("--admin")
    gitea_cli(*cmd)


def make_token() -> str:
    token_name = "hab-seed-" + datetime.now().strftime("%Y%m%d%H%M%S")
    proc = gitea_cli("admin", "user", "generate-access-token", "--username", OWNER, "--token-name", token_name, "--raw", "--scopes", "write:user,write:repository,write:issue,read:repository")
    token = proc.stdout.strip().splitlines()[-1].strip()
    if not token:
        raise RuntimeError("failed to generate seed token")
    return token


def api(token: str, method: str, path: str, payload: dict[str, object] | None = None, allow: set[int] | None = None):
    allow = allow or {200, 201, 204}
    cmd = ["docker", "exec", "-i", CONTAINER, "curl", "-sS", "-X", method, "-H", f"Authorization: token {token}", "-H", "Content-Type: application/json"]
    input_text = None
    if payload is not None:
        cmd.extend(["--data-binary", "@-"])
        input_text = json.dumps(payload)
    cmd.extend(["-w", "\n%{http_code}", "http://127.0.0.1:3000/api/v1" + path])
    proc = run(cmd, input_text=input_text, timeout=60)
    if "\n" in proc.stdout:
        body, code_text = proc.stdout.rsplit("\n", 1)
    else:
        body, code_text = "", proc.stdout.strip()
    code = int(code_text.strip() or "0")
    if code not in allow:
        raise RuntimeError(f"API {method} {path} returned HTTP {code}: {body[:300]}")
    try:
        data = json.loads(body) if body.strip() else None
    except json.JSONDecodeError:
        data = body
    return code, data


def repo_path(repo: str) -> str:
    return f"/repos/{quote(OWNER)}/{quote(repo)}"


def ensure_repo(token: str, repo: str, description: str) -> None:
    payload = {"name": repo, "description": description, "private": False, "auto_init": True, "default_branch": "main"}
    api(token, "POST", "/user/repos", payload, allow={200, 201, 409})


def upsert_file(token: str, repo: str, rel_path: str, content: str) -> None:
    encoded_path = quote(rel_path, safe="/")
    sha = None
    code, data = api(token, "GET", repo_path(repo) + f"/contents/{encoded_path}?ref=main", allow={200, 404})
    if code == 200 and isinstance(data, dict):
        sha = data.get("sha")
    payload = {
        "branch": "main",
        "message": f"seed {rel_path}",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    method = "PUT" if sha else "POST"
    if sha:
        payload["sha"] = sha
    api(token, method, repo_path(repo) + f"/contents/{encoded_path}", payload, allow={200, 201})


def ensure_issue(token: str, repo: str, title: str) -> None:
    _, issues = api(token, "GET", repo_path(repo) + "/issues?state=all", allow={200})
    if isinstance(issues, list) and any(item.get("title") == title for item in issues if isinstance(item, dict)):
        return
    api(token, "POST", repo_path(repo) + "/issues", {"title": title, "body": "Seeded benchmark issue for service-context evidence."}, allow={201})


def main() -> int:
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    compose_up()
    ensure_user("alice.dev", "alice.dev@example.invalid", admin=True)
    ensure_user("bob.ops", "bob.ops@example.invalid", admin=False)
    token = make_token()
    seeded_files: list[str] = []
    seeded_issues: list[str] = []
    for repo, spec in REPOS.items():
        ensure_repo(token, repo, str(spec["description"]))
        for rel_path, content in spec["files"].items():
            upsert_file(token, repo, rel_path, content)
            seeded_files.append(f"{repo}/{rel_path}")
        for title in spec["issues"]:
            ensure_issue(token, repo, title)
            seeded_issues.append(f"{repo}#{title}")
    summary = {
        "schema_version": "gitea-seed-summary-v1",
        "seeded_at": datetime.now().isoformat(timespec="seconds"),
        "users": ["alice.dev", "bob.ops"],
        "repos": sorted(REPOS),
        "files": seeded_files,
        "issues": seeded_issues,
        "secret_handling": "Seed token was generated at runtime and not written to disk.",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Gitea Seed Report", "", "Status: PASS", "", "Seeded Node D real-service content into the running Gitea container.", "", "Seeded users:", ""]
    lines.extend(f"- {user}" for user in summary["users"])
    lines.extend(["", "Seeded repositories:", ""])
    lines.extend(f"- {repo}" for repo in summary["repos"])
    lines.extend(["", "Seeded files:", ""])
    lines.extend(f"- {item}" for item in seeded_files)
    lines.extend(["", "Evidence:", "", f"- Summary artifact: `{SUMMARY.relative_to(ROOT)}`", "", "No runtime token or password is written to this report."])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
