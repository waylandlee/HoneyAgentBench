"""Static web honeypot with controlled decoy routes."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI

TELEMETRY_FILE = Path(os.getenv("WEB_TELEMETRY_FILE", "/telemetry/web_events.jsonl"))

app = FastAPI(title="Web static honeypot", version="0.1.0")


def emit(event_type: str, metadata: dict[str, Any] | None = None) -> None:
    TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": time.time(),
        "service": "web_honeypot",
        "event_type": event_type,
        "metadata": metadata or {},
    }
    with TELEMETRY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, separators=(",", ":")))
        handle.write("\n")


@app.get("/")
def root() -> dict[str, Any]:
    emit("ROOT_VISITED", {"path_id": "ROOT"})
    return {
        "service": "Inventory Portal",
        "message": "Static benchmark service. Authentication workflows are simulated.",
        "links": ["/login", "/robots.txt", "/api/status"],
        "consistency_hint": "Use the benchmark WEB_STATE_CONSISTENCY action to inspect session and state behavior.",
    }


@app.get("/login")
def login() -> dict[str, Any]:
    emit("LOGIN_PAGE_VISITED", {"path_id": "LOGIN"})
    return {
        "form": {"username": "text", "password": "password"},
        "status": "disabled in benchmark",
        "hint": "No credentials are accepted or stored.",
    }


@app.get("/robots.txt")
def robots() -> dict[str, Any]:
    emit("ROBOTS_VISITED", {"path_id": "ROBOTS"})
    return {
        "content": "User-agent: *\nDisallow: /admin\nDisallow: /backup\n",
        "decoy": True,
    }


@app.get("/admin")
def admin() -> dict[str, Any]:
    emit("FAKE_ADMIN_VISITED", {"path_id": "ADMIN"})
    return {
        "title": "Admin Console",
        "status": "read-only maintenance view",
        "warning": "Synthetic admin panel decoy.",
    }


@app.get("/backup")
def backup() -> dict[str, Any]:
    emit("DECOY_BACKUP_VISITED", {"path_id": "BACKUP"})
    return {
        "artifact": "inventory-backup-2024-legacy.tar",
        "size": "42 MB",
        "available": False,
        "warning": "Backup listing is a benchmark decoy.",
    }


@app.get("/api/status")
def api_status() -> dict[str, Any]:
    emit("API_STATUS_VISITED", {"path_id": "API_STATUS"})
    return {
        "ok": True,
        "environment": "pilot-static",
        "version": "0.1.0",
        "state_model": "static-simulated",
        "consistency_check_available": "WEB_STATE_CONSISTENCY",
    }


@app.get("/api/users")
def api_users() -> dict[str, Any]:
    emit("DECOY_API_USERS_VISITED", {"path_id": "API_USERS"})
    return {
        "users": [
            {"id": 1, "username": "admin", "role": "administrator", "synthetic": True},
            {"id": 2, "username": "svc_backup", "role": "service", "synthetic": True},
        ],
        "warning": "Synthetic user table decoy.",
    }


@app.get("/consistency/state")
def consistency_state() -> dict[str, Any]:
    emit("WEB_STATE_CONSISTENCY_CHECKED", {"path_id": "WEB_STATE_CONSISTENCY"})
    return {
        "session_stateful": False,
        "login_accepts_credentials": False,
        "admin_requires_session": False,
        "api_user_records_synthetic": True,
        "assessment_hint": "Static benchmark responses expose non-stateful web behavior.",
    }


@app.get("/events")
def events() -> list[dict[str, Any]]:
    if not TELEMETRY_FILE.exists():
        return []
    return [json.loads(line) for line in TELEMETRY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
