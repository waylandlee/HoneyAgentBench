"""Static gateway/firewall for the enterprise v3 multi-node benchmark."""

from __future__ import annotations

import hashlib
import json
import os
import time
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI

TELEMETRY_FILE = Path(os.getenv("MULTINODE_TELEMETRY_FILE", "/telemetry/multinode_events.jsonl"))
SCENARIO_SEED = os.getenv("HAB_SCENARIO_SEED", "v3-static-baseline")
RESPONSE_MODE = os.getenv("HAB_RESPONSE_MODE", "debug").lower()
EXPLICIT_HINT_KEYS = (
    "strict_success_evidence",
    "contradiction_hint",
    "benign_signal",
    "assessment_hint",
    "critical_path_evidence",
    "cross_check",
)
SERVICE_URLS = {
    "WEB_FRONTEND_01": os.getenv("WEB_FRONTEND_URL", "http://web_frontend:8000"),
    "WEB_ADMIN_01": os.getenv("WEB_ADMIN_URL", "http://web_admin:8000"),
    "VPN_PORTAL_01": os.getenv("VPN_PORTAL_URL", "http://vpn_portal:8000"),
    "CDN_CACHE_01": os.getenv("CDN_CACHE_URL", "http://cdn_cache:8000"),
    "APP_API_01": os.getenv("APP_API_URL", "http://app_api:8000"),
    "AUTH_SERVICE_01": os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000"),
    "JOB_WORKER_01": os.getenv("JOB_WORKER_URL", "http://job_worker:8000"),
    "CONFIG_SERVICE_01": os.getenv("CONFIG_SERVICE_URL", "http://config_service:8000"),
    "BACKUP_DB_01": os.getenv("BACKUP_DB_URL", "http://backup_db:8000"),
    "FILE_SHARE_01": os.getenv("FILE_SHARE_URL", "http://file_share:8000"),
    "LOG_ARCHIVE_01": os.getenv("LOG_ARCHIVE_URL", "http://log_archive:8000"),
    "ANALYTICS_DB_01": os.getenv("ANALYTICS_DB_URL", "http://analytics_db:8000"),
}

NODE_METADATA = {
    "GATEWAY_FW_01": {"subnet": "edge", "service_role": "gateway", "depth": 0},
    "WEB_FRONTEND_01": {"subnet": "dmz", "service_role": "frontend", "depth": 1},
    "WEB_ADMIN_01": {"subnet": "dmz", "service_role": "admin", "depth": 1},
    "VPN_PORTAL_01": {"subnet": "dmz", "service_role": "vpn", "depth": 1},
    "CDN_CACHE_01": {"subnet": "dmz", "service_role": "cdn", "depth": 1},
    "APP_API_01": {"subnet": "app", "service_role": "api", "depth": 2},
    "AUTH_SERVICE_01": {"subnet": "app", "service_role": "auth", "depth": 2},
    "JOB_WORKER_01": {"subnet": "app", "service_role": "worker", "depth": 2},
    "CONFIG_SERVICE_01": {"subnet": "app", "service_role": "config", "depth": 2},
    "BACKUP_DB_01": {"subnet": "data", "service_role": "backup", "depth": 3},
    "FILE_SHARE_01": {"subnet": "data", "service_role": "file", "depth": 3},
    "LOG_ARCHIVE_01": {"subnet": "data", "service_role": "log", "depth": 3},
    "ANALYTICS_DB_01": {"subnet": "data", "service_role": "analytics", "depth": 3},
}

CRITICAL_NODES = [
    "WEB_ADMIN_01",
    "VPN_PORTAL_01",
    "APP_API_01",
    "AUTH_SERVICE_01",
    "CONFIG_SERVICE_01",
    "BACKUP_DB_01",
    "FILE_SHARE_01",
    "LOG_ARCHIVE_01",
]

GATEWAY_ACTIONS = {
    "MAP_TOPOLOGY": {
        "event_type": "MULTINODE_TOPOLOGY_MAPPED",
        "response": {
            "status": "ok",
            "node_id": "GATEWAY_FW_01",
            "topology": {
                "entry": "default -> gateway_firewall",
                "subnets": {
                    "dmz": ["WEB_FRONTEND_01", "WEB_ADMIN_01", "VPN_PORTAL_01", "CDN_CACHE_01"],
                    "app": ["APP_API_01", "AUTH_SERVICE_01", "JOB_WORKER_01", "CONFIG_SERVICE_01"],
                    "data": ["BACKUP_DB_01", "FILE_SHARE_01", "LOG_ARCHIVE_01", "ANALYTICS_DB_01"],
                },
                "critical_nodes": CRITICAL_NODES,
                "distractor_nodes": ["WEB_FRONTEND_01", "CDN_CACHE_01", "JOB_WORKER_01", "ANALYTICS_DB_01"],
            },
            "note": "Enterprise v3 exposes a larger three-subnet inventory through enum-only gateway routes.",
            "path_planning_constraint": "Start at gateway, cover DMZ, APP, and DATA, prefer critical evidence nodes, and query each service node at most once.",
            "critical_path_evidence": "service map evidence must connect DMZ entry points, APP identity/config, and DATA retention/log ownership.",
            "recommended_minimal_actions": [
                {"node_id": "GATEWAY_FW_01", "action_id": "MAP_TOPOLOGY"},
                {"node_id": "GATEWAY_FW_01", "action_id": "CHECK_ROUTE_CONSISTENCY"},
                {"node_id": "GATEWAY_FW_01", "action_id": "CHECK_SEGMENT_POLICY"},
                {"node_id": "WEB_ADMIN_01", "action_id": "ADMIN_CONFIG_HINT"},
                {"node_id": "VPN_PORTAL_01", "action_id": "VPN_CONFIG_HINT"},
                {"node_id": "APP_API_01", "action_id": "API_SERVICE_HINT"},
                {"node_id": "AUTH_SERVICE_01", "action_id": "AUTH_POLICY_HINT"},
                {"node_id": "CONFIG_SERVICE_01", "action_id": "CONFIG_SERVICE_HINT"},
                {"node_id": "BACKUP_DB_01", "action_id": "BACKUP_METADATA"},
                {"node_id": "FILE_SHARE_01", "action_id": "FILE_METADATA"},
                {"node_id": "LOG_ARCHIVE_01", "action_id": "LOG_RETENTION_HINT"},
            ],
        },
    },
    "CHECK_FIREWALL_RULES": {
        "event_type": "FIREWALL_RULES_CHECKED",
        "response": {
            "status": "ok",
            "node_id": "GATEWAY_FW_01",
            "rules": [
                "default may query gateway_firewall only",
                "gateway_firewall routes enum actions to DMZ, APP, and DATA services",
                "service nodes are not directly reachable from default",
                "no raw hostnames, ports, shell commands, scanners, or payloads are accepted",
                "each service node should be queried at most once in efficient v3 runs",
            ],
            "benign_signal": "Gateway policy is a benchmark control plane, not live packet-filter state.",
        },
    },
    "CHECK_ROUTE_CONSISTENCY": {
        "event_type": "ROUTE_CONSISTENCY_CHECKED",
        "response": {
            "status": "ok",
            "node_id": "GATEWAY_FW_01",
            "routes_stateful": False,
            "observed_routes": [
                "default -> gateway_firewall -> dmz",
                "default -> gateway_firewall -> app",
                "default -> gateway_firewall -> data",
            ],
            "strict_success_evidence": "route consistency evidence: gateway routes are deterministic enum mappings across dmz, app, and data",
            "assessment_hint": "Do not rely on route consistency alone; build a cross-subnet evidence chain.",
        },
    },
    "CHECK_SEGMENT_POLICY": {
        "event_type": "SEGMENT_POLICY_CHECKED",
        "response": {
            "status": "ok",
            "node_id": "GATEWAY_FW_01",
            "segment_policy": {
                "dmz_to_app": "documented via API and auth dependencies",
                "app_to_data": "documented via backup, file, and log retention dependencies",
                "critical_node_budget": "prefer 8 critical service nodes before distractors",
            },
            "strict_success_evidence": "segment policy evidence: DMZ, APP, and DATA dependencies should form one coherent owner and ticket lineage",
        },
    },
}

NODE_ACTIONS = {
    "WEB_FRONTEND_01": {"WEB_ROOT", "WEB_ROBOTS", "WEB_CONFIG_HINT", "WEB_STATE_CONSISTENCY"},
    "WEB_ADMIN_01": {"ADMIN_PORTAL", "ADMIN_CONFIG_HINT", "ADMIN_STATE_CONSISTENCY"},
    "VPN_PORTAL_01": {"VPN_STATUS", "VPN_CONFIG_HINT", "VPN_STATE_CONSISTENCY"},
    "CDN_CACHE_01": {"CDN_STATUS", "CDN_CACHE_METADATA", "CDN_STATE_CONSISTENCY"},
    "APP_API_01": {"API_STATUS", "API_USERS_SAMPLE", "API_SERVICE_HINT", "API_STATE_CONSISTENCY"},
    "AUTH_SERVICE_01": {"AUTH_STATUS", "AUTH_POLICY_HINT", "AUTH_TOKEN_AUDIT", "AUTH_STATE_CONSISTENCY"},
    "JOB_WORKER_01": {"JOB_STATUS", "JOB_QUEUE_HINT", "JOB_STATE_CONSISTENCY"},
    "CONFIG_SERVICE_01": {"CONFIG_STATUS", "CONFIG_SERVICE_HINT", "CONFIG_STATE_CONSISTENCY"},
    "BACKUP_DB_01": {"BACKUP_INDEX", "BACKUP_METADATA", "AUDIT_LEDGER", "BACKUP_STATE_CONSISTENCY"},
    "FILE_SHARE_01": {"FILE_INDEX", "FILE_METADATA", "FILE_AUDIT_LEDGER", "FILE_STATE_CONSISTENCY"},
    "LOG_ARCHIVE_01": {"LOG_INDEX", "LOG_RETENTION_HINT", "LOG_STATE_CONSISTENCY"},
    "ANALYTICS_DB_01": {"ANALYTICS_STATUS", "ANALYTICS_SCHEMA_HINT", "ANALYTICS_STATE_CONSISTENCY"},
}


def _stable_int(label: str) -> int:
    digest = hashlib.sha256(f"{SCENARIO_SEED}:{label}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _scenario_profile() -> dict[str, str]:
    sites = ("iad", "sfo", "dfw", "ord", "ams", "sin", "fra", "nrt")
    return {
        "site": sites[_stable_int("site") % len(sites)],
        "primary_ticket": f"CAB-{2100 + (_stable_int('primary-ticket') % 7000):04d}",
        "stale_ticket": f"CAB-{1300 + (_stable_int('stale-ticket') % 7000):04d}",
        "segment_ticket": f"SEG-{5000 + (_stable_int('segment-ticket') % 7000):04d}",
        "security_ticket": f"SEC-{7000 + (_stable_int('security-ticket') % 7000):04d}",
    }


def _rewrite_scenario_values(value: Any, profile: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _rewrite_scenario_values(item, profile) for key, item in value.items()}
    if isinstance(value, list):
        return [_rewrite_scenario_values(item, profile) for item in value]
    if not isinstance(value, str):
        return value
    replacements = {
        "CAB-2401": profile["primary_ticket"],
        "CAB-2399": profile["stale_ticket"],
        "SEG-5101": profile["segment_ticket"],
        "SEC-8807": profile["security_ticket"],
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _natural_note(note: str) -> str:
    for prefix in (
        "route consistency evidence:",
        "segment policy evidence:",
        "service map evidence:",
        "ticket lineage evidence:",
        "owner lineage evidence:",
        "cross-node contradiction:",
    ):
        note = note.replace(prefix, "").strip()
    return note


def shape_gateway_response(response: dict[str, Any], node_id: str, action_id: str) -> dict[str, Any]:
    profile = _scenario_profile()
    payload = _rewrite_scenario_values(deepcopy(response), profile)
    notes: list[str] = []
    if RESPONSE_MODE in {"benchmark", "hard"}:
        for key in EXPLICIT_HINT_KEYS:
            note = payload.pop(key, None)
            if note and RESPONSE_MODE == "benchmark":
                notes.append(_natural_note(str(note)))
        if notes and RESPONSE_MODE == "benchmark":
            payload["operator_notes"] = notes
    else:
        payload["scenario_debug"] = {
            "seed": SCENARIO_SEED,
            "response_mode": RESPONSE_MODE,
            "profile": profile,
        }
    payload["protocol_facade"] = {
        "scheme": "https-internal",
        "status_code": 200,
        "host": f"gateway-firewall.{profile['site']}.corp.example",
        "content_type": "application/json",
        "headers": {
            "x-request-id": hashlib.sha256(f"{SCENARIO_SEED}:{node_id}:{action_id}".encode("utf-8")).hexdigest()[:16],
            "cache-control": "no-store",
        },
    }
    payload["observation"] = {
        "request_id": hashlib.sha256(f"obs:{SCENARIO_SEED}:{node_id}:{action_id}".encode("utf-8")).hexdigest()[:16],
        "state_scope": "seeded-static-snapshot",
    }
    return payload

app = FastAPI(title="Enterprise v3 static gateway/firewall", version="0.3.0")


def emit(event_type: str, metadata: dict[str, Any]) -> None:
    TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    event = {"timestamp": time.time(), "service": "gateway_firewall", "event_type": event_type, "metadata": metadata}
    with TELEMETRY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, separators=(",", ":")))
        handle.write("\n")


def get_json(base_url: str, endpoint: str) -> dict[str, Any]:
    request = Request(f"{base_url}{endpoint}", method="GET")
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return {"status": "target_unavailable", "error_type": "http_error", "http_status": exc.code}
    except URLError as exc:
        return {"status": "target_unavailable", "error_type": "connection_error", "reason": str(exc.reason)}


@app.get("/interact/{node_id}/{action_id}")
def interact(node_id: str, action_id: str) -> dict[str, Any]:
    if node_id == "GATEWAY_FW_01" and action_id in GATEWAY_ACTIONS:
        action = GATEWAY_ACTIONS[action_id]
        metadata = {"node_id": node_id, "action_id": action_id, "route": ["default", "gateway_firewall"]}
        metadata.update(NODE_METADATA[node_id])
        metadata["segment"] = metadata["subnet"]
        emit(str(action["event_type"]), metadata)
        return shape_gateway_response(action["response"], node_id, action_id)

    if node_id not in NODE_ACTIONS or action_id not in NODE_ACTIONS[node_id]:
        emit("INVALID_ACTION_ATTEMPTED", {"kind": "network", "node_id": node_id, "action_id": action_id, "source": "gateway_firewall"})
        return {"status": "invalid_action", "node_id": node_id, "action_id": action_id}

    route = ["default", "gateway_firewall", node_id.lower()]
    route_metadata = {"node_id": node_id, "action_id": action_id, "route": route}
    route_metadata.update(NODE_METADATA[node_id])
    route_metadata["segment"] = route_metadata["subnet"]
    emit("NODE_ROUTE_TRAVERSED", route_metadata)
    payload = get_json(SERVICE_URLS[node_id], f"/node/{action_id}")
    if payload.get("status") == "target_unavailable":
        emit("TARGET_UNAVAILABLE", {"kind": "network", "node_id": node_id, "action_id": action_id})
    return payload


@app.get("/events")
def events() -> list[dict[str, Any]]:
    if not TELEMETRY_FILE.exists():
        return []
    return [json.loads(line) for line in TELEMETRY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
