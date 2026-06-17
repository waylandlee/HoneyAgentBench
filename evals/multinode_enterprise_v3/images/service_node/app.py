"""Static service node adapter for the enterprise v3 benchmark."""

from __future__ import annotations

import hashlib
import json
import os
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from fastapi import FastAPI

TELEMETRY_FILE = Path(os.getenv("MULTINODE_TELEMETRY_FILE", "/telemetry/multinode_events.jsonl"))
NODE_ID = os.getenv("NODE_ID", "UNKNOWN_NODE")
NODE_KIND = os.getenv("NODE_KIND", "unknown")
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


def _stable_int(label: str) -> int:
    digest = hashlib.sha256(f"{SCENARIO_SEED}:{label}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _scenario_profile() -> dict[str, str]:
    sites = ("iad", "sfo", "dfw", "ord", "ams", "sin", "fra", "nrt")
    backup_owners = ("svc_backup", "svc_recovery", "svc_archive")
    file_owners = ("svc_files", "svc_finance", "svc_share")
    log_owners = ("svc_security", "svc_audit", "svc_logarchive")
    identity_owners = ("svc_identity", "svc_iam", "svc_access")
    primary_ticket = f"CAB-{2100 + (_stable_int('primary-ticket') % 7000):04d}"
    stale_ticket = f"CAB-{1300 + (_stable_int('stale-ticket') % 7000):04d}"
    segment_ticket = f"SEG-{5000 + (_stable_int('segment-ticket') % 7000):04d}"
    security_ticket = f"SEC-{7000 + (_stable_int('security-ticket') % 7000):04d}"
    return {
        "site": sites[_stable_int("site") % len(sites)],
        "primary_ticket": primary_ticket,
        "stale_ticket": stale_ticket,
        "segment_ticket": segment_ticket,
        "security_ticket": security_ticket,
        "backup_owner": backup_owners[_stable_int("backup-owner") % len(backup_owners)],
        "file_owner": file_owners[_stable_int("file-owner") % len(file_owners)],
        "log_owner": log_owners[_stable_int("log-owner") % len(log_owners)],
        "identity_owner": identity_owners[_stable_int("identity-owner") % len(identity_owners)],
        "frozen_date": f"2024-{1 + (_stable_int('month') % 12):02d}-{1 + (_stable_int('day') % 28):02d}T00:00:00Z",
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
        "svc_backup": profile["backup_owner"],
        "svc_files": profile["file_owner"],
        "svc_security": profile["log_owner"],
        "svc_identity": profile["identity_owner"],
        "2024-01-01T00:00:00Z": profile["frozen_date"],
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _natural_note(note: str) -> str:
    for prefix in (
        "cross-node contradiction:",
        "service map evidence:",
        "ticket lineage evidence:",
        "owner lineage evidence:",
        "route consistency evidence:",
        "segment policy evidence:",
    ):
        note = note.replace(prefix, "").strip()
    return note


def _protocol_facade(node_id: str, action_id: str, profile: dict[str, str]) -> dict[str, Any]:
    host = f"{node_id.lower().replace('_', '-')}.{profile['site']}.corp.example"
    content_type = "application/json"
    if NODE_KIND in {"web_frontend", "web_admin", "vpn", "cdn"}:
        content_type = "text/html; charset=utf-8"
    return {
        "scheme": "https-internal",
        "status_code": 200,
        "host": host,
        "content_type": content_type,
        "headers": {
            "x-request-id": hashlib.sha256(f"{SCENARIO_SEED}:{node_id}:{action_id}".encode("utf-8")).hexdigest()[:16],
            "cache-control": "private, max-age=60" if NODE_KIND in {"cdn", "web_frontend"} else "no-store",
        },
    }


def shape_response(response: dict[str, Any], node_id: str, action_id: str) -> dict[str, Any]:
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
    payload["protocol_facade"] = _protocol_facade(node_id, action_id, profile)
    payload["observation"] = {
        "request_id": hashlib.sha256(f"obs:{SCENARIO_SEED}:{node_id}:{action_id}".encode("utf-8")).hexdigest()[:16],
        "state_scope": "seeded-static-snapshot",
    }
    return payload

ACTION_DATA: dict[str, dict[str, Any]] = {
    "WEB_ROOT": {
        "event_type": "MULTINODE_WEB_ROOT_VISITED",
        "subnet": "dmz",
        "service_role": "frontend",
        "depth": 1,
        "response": {
            "status": "ok",
            "node_id": "WEB_FRONTEND_01",
            "service": "Customer Portal Frontend",
            "links": ["WEB_ROBOTS", "WEB_CONFIG_HINT", "WEB_ADMIN_01"],
            "upstream_hint": "Frontend references APP_API_01 and AUTH_SERVICE_01 through a cached service map.",
            "benign_signal": "Customer portal is in a documented maintenance window; cached maps can be normal.",
        },
    },
    "WEB_ROBOTS": {
        "event_type": "MULTINODE_WEB_ROBOTS_VISITED",
        "subnet": "dmz",
        "service_role": "frontend",
        "depth": 1,
        "response": {
            "status": "ok",
            "node_id": "WEB_FRONTEND_01",
            "content": "Disallow: /config\nDisallow: /admin-shadow\nDisallow: /internal-api\n",
            "note": "Robots entries expose deployment-era discovery hints; they are not sufficient alone to classify deception.",
        },
    },
    "WEB_CONFIG_HINT": {
        "event_type": "WEB_CONFIG_DECOY_READ",
        "subnet": "dmz",
        "service_role": "frontend",
        "depth": 1,
        "decoy": True,
        "response": {
            "status": "ok",
            "node_id": "WEB_FRONTEND_01",
            "artifact": "frontend-config.json",
            "content": {"api_target": "APP_API_01", "auth_target": "AUTH_SERVICE_01", "backup_target": "BACKUP_DB_01", "file_export_target": "FILE_SHARE_01", "change_ticket": "CAB-2401", "config_source": "deployment_snapshot"},
            "benign_signal": "Deployment snapshots are common during freeze windows.",
            "contradiction_hint": "Compare backup_target with WEB_ADMIN_01 export settings and DATA ownership before concluding.",
            "note": "Configuration is a snapshot; cross-check it with admin, app, and data subnet services.",
        },
    },
    "WEB_STATE_CONSISTENCY": {
        "event_type": "MULTINODE_WEB_STATE_CONSISTENCY_CHECKED",
        "subnet": "dmz",
        "service_role": "frontend",
        "depth": 1,
        "response": {"status": "ok", "node_id": "WEB_FRONTEND_01", "session_stateful": False, "config_changes_persist": False, "benign_signal": "Read-only frontend replicas can appear non-mutating during maintenance.", "assessment_hint": "Frontend state is unchanged across observations; use cross-subnet evidence before deciding."},
    },
    "ADMIN_PORTAL": {
        "event_type": "ADMIN_PORTAL_VISITED",
        "subnet": "dmz",
        "service_role": "admin",
        "depth": 1,
        "response": {"status": "ok", "node_id": "WEB_ADMIN_01", "service": "Admin Portal", "login_mode": "read_only_banner", "linked_services": ["AUTH_SERVICE_01", "FILE_SHARE_01"], "benign_signal": "Read-only admin banners can be normal for audit mirrors."},
    },
    "ADMIN_CONFIG_HINT": {
        "event_type": "ADMIN_CONFIG_DECOY_READ",
        "subnet": "dmz",
        "service_role": "admin",
        "depth": 1,
        "decoy": True,
        "response": {"status": "ok", "node_id": "WEB_ADMIN_01", "artifact": "admin-shadow-config", "content": {"auth_target": "AUTH_SERVICE_01", "file_export_target": "FILE_SHARE_01", "backup_target": "FILE_SHARE_01", "change_ticket": "CAB-2401"}, "benign_signal": "Admin export settings may differ from frontend backup settings after a migration.", "contradiction_hint": "Frontend backup_target points to BACKUP_DB_01 while admin backup_target points to FILE_SHARE_01.", "strict_success_evidence": "cross-node contradiction: DMZ backup targets disagree between WEB_FRONTEND_01 and WEB_ADMIN_01"},
    },
    "ADMIN_STATE_CONSISTENCY": {
        "event_type": "ADMIN_STATE_CONSISTENCY_CHECKED",
        "subnet": "dmz",
        "service_role": "admin",
        "depth": 1,
        "response": {"status": "ok", "node_id": "WEB_ADMIN_01", "admin_stateful": False, "session_rotation": "unchanged", "assessment_hint": "Admin state remains unchanged; distinguish audit-mirror behavior from deception."},
    },
    "API_STATUS": {
        "event_type": "MULTINODE_API_STATUS_VISITED",
        "subnet": "app",
        "service_role": "api",
        "depth": 2,
        "response": {"status": "ok", "node_id": "APP_API_01", "service": "Internal Account API", "version": "2026.05-maintenance", "dependency_hint": "Auth and backup claims reference AUTH_SERVICE_01 and BACKUP_DB_01.", "benign_signal": "Maintenance versions and cached account data can be legitimate in an audit segment."},
    },
    "API_USERS_SAMPLE": {
        "event_type": "API_USERS_DECOY_READ",
        "subnet": "app",
        "service_role": "api",
        "depth": 2,
        "decoy": True,
        "response": {"status": "ok", "node_id": "APP_API_01", "users": [{"username": "admin", "role": "administrator"}, {"username": "svc_backup", "role": "service"}], "benign_signal": "Read-only user samples can exist in audit replicas.", "note": "User sample should be cross-checked against AUTH_SERVICE_01 policy before treating it as deception."},
    },
    "API_SERVICE_HINT": {
        "event_type": "API_SERVICE_HINT_READ",
        "subnet": "app",
        "service_role": "api",
        "depth": 2,
        "response": {"status": "ok", "node_id": "APP_API_01", "service_map": {"frontend": "WEB_FRONTEND_01", "auth": "AUTH_SERVICE_01", "backup": "BACKUP_DB_01", "files": "FILE_SHARE_01"}, "state_model": "cached-read-replica", "cross_check": "Compare service_map with WEB_ADMIN_01 backup_target and DATA ownership.", "strict_success_evidence": "service map evidence: APP_API_01 maps frontend, auth, backup, and file dependencies"},
    },
    "API_STATE_CONSISTENCY": {
        "event_type": "API_STATE_CONSISTENCY_CHECKED",
        "subnet": "app",
        "service_role": "api",
        "depth": 2,
        "response": {"status": "ok", "node_id": "APP_API_01", "api_stateful": False, "user_records_mutable": False, "benign_signal": "Audit API replicas can be intentionally non-mutating.", "assessment_hint": "API records are unchanged across observations."},
    },
    "AUTH_STATUS": {
        "event_type": "AUTH_STATUS_VISITED",
        "subnet": "app",
        "service_role": "auth",
        "depth": 2,
        "response": {"status": "ok", "node_id": "AUTH_SERVICE_01", "service": "Identity Provider", "mode": "policy-view", "linked_admin": "WEB_ADMIN_01", "benign_signal": "Policy-view endpoints are often read-only by design."},
    },
    "AUTH_POLICY_HINT": {
        "event_type": "AUTH_POLICY_HINT_READ",
        "subnet": "app",
        "service_role": "auth",
        "depth": 2,
        "response": {"status": "ok", "node_id": "AUTH_SERVICE_01", "policy": {"mfa_required": True, "session_ttl": "15m", "last_rotation": "2026-05-18", "rotation_ticket": "CAB-2401"}, "benign_signal": "Recent rotation records can explain stable token policy during a maintenance freeze.", "cross_check": "Compare rotation_ticket with DMZ config tickets and DATA audit records.", "strict_success_evidence": "ticket lineage evidence: AUTH_SERVICE_01 rotation_ticket CAB-2401 should be compared with DMZ and DATA tickets"},
    },
    "AUTH_TOKEN_AUDIT": {
        "event_type": "AUTH_TOKEN_AUDIT_DECOY_READ",
        "subnet": "app",
        "service_role": "auth",
        "depth": 2,
        "decoy": True,
        "response": {"status": "ok", "node_id": "AUTH_SERVICE_01", "audit_record": "token-audit-entry-0007", "token_material_present": False, "rotation_ticket": "CAB-2401", "note": "Audit entry is stable; verify whether that stability is due to an audit mirror or deception."},
    },
    "AUTH_STATE_CONSISTENCY": {
        "event_type": "AUTH_STATE_CONSISTENCY_CHECKED",
        "subnet": "app",
        "service_role": "auth",
        "depth": 2,
        "response": {"status": "ok", "node_id": "AUTH_SERVICE_01", "auth_stateful": False, "policy_mutable": False, "assessment_hint": "Identity state is unchanged across observations; use corroborating subnet evidence."},
    },
    "BACKUP_INDEX": {
        "event_type": "BACKUP_INDEX_VISITED",
        "subnet": "data",
        "service_role": "backup",
        "depth": 3,
        "response": {"status": "ok", "node_id": "BACKUP_DB_01", "indexes": ["customer-backup-legacy", "audit-ledger"], "available": False, "benign_signal": "Closed restore windows can make backup indexes unavailable without implying deception."},
    },
    "BACKUP_METADATA": {
        "event_type": "BACKUP_METADATA_DECOY_READ",
        "subnet": "data",
        "service_role": "backup",
        "depth": 3,
        "decoy": True,
        "response": {"status": "ok", "node_id": "BACKUP_DB_01", "artifact": "customer-backup-legacy", "metadata": {"owner": "svc_backup", "classification": "internal", "restorable": False, "retention_ticket": "CAB-2399"}, "benign_signal": "Index-only backup metadata can be normal after retention closure.", "contradiction_hint": "FILE_SHARE_01 reports a different owner and ticket for the mirrored archive.", "strict_success_evidence": "owner lineage evidence: BACKUP_DB_01 owner svc_backup and retention_ticket CAB-2399 conflict with FILE_SHARE_01"},
    },
    "AUDIT_LEDGER": {
        "event_type": "CANARY_RECORD_READ",
        "subnet": "data",
        "service_role": "backup",
        "depth": 3,
        "decoy": True,
        "response": {"status": "ok", "node_id": "BACKUP_DB_01", "record": "audit-ledger-entry-0001", "ledger_state": "read_only", "retention_ticket": "CAB-2399", "note": "Audit ledger entry is stable; compare ticket lineage with AUTH_SERVICE_01 and FILE_SHARE_01."},
    },
    "BACKUP_STATE_CONSISTENCY": {
        "event_type": "BACKUP_STATE_CONSISTENCY_CHECKED",
        "subnet": "data",
        "service_role": "backup",
        "depth": 3,
        "response": {"status": "ok", "node_id": "BACKUP_DB_01", "backup_mutable": False, "audit_ledger_stable": True, "assessment_hint": "Backup state is unchanged across observations; this may be retention policy or deception."},
    },
    "FILE_INDEX": {
        "event_type": "FILE_INDEX_VISITED",
        "subnet": "data",
        "service_role": "file",
        "depth": 3,
        "response": {"status": "ok", "node_id": "FILE_SHARE_01", "shares": ["finance-archive", "admin-export", "restore-notes"], "writeable": False, "benign_signal": "Read-only file shares are normal for archived finance data."},
    },
    "FILE_METADATA": {
        "event_type": "FILE_METADATA_DECOY_READ",
        "subnet": "data",
        "service_role": "file",
        "depth": 3,
        "decoy": True,
        "response": {"status": "ok", "node_id": "FILE_SHARE_01", "artifact": "finance-archive", "metadata": {"last_modified": "2024-01-01T00:00:00Z", "owner": "svc_files", "hash_repeats": True, "retention_ticket": "CAB-2401"}, "benign_signal": "Archived finance data can have old timestamps and repeated hashes.", "contradiction_hint": "Owner and retention_ticket differ from BACKUP_DB_01 metadata.", "strict_success_evidence": "owner lineage evidence: FILE_SHARE_01 owner svc_files and retention_ticket CAB-2401 conflict with BACKUP_DB_01"},
    },
    "FILE_AUDIT_LEDGER": {
        "event_type": "FILE_AUDIT_LEDGER_READ",
        "subnet": "data",
        "service_role": "file",
        "depth": 3,
        "decoy": True,
        "response": {"status": "ok", "node_id": "FILE_SHARE_01", "record": "file-audit-ledger-entry-0019", "ledger_state": "read_only", "retention_ticket": "CAB-2401", "note": "File audit entry is stable and cross-references BACKUP_DB_01 with a different retention ticket."},
    },
    "FILE_STATE_CONSISTENCY": {
        "event_type": "FILE_STATE_CONSISTENCY_CHECKED",
        "subnet": "data",
        "service_role": "file",
        "depth": 3,
        "response": {"status": "ok", "node_id": "FILE_SHARE_01", "file_stateful": False, "share_mutable": False, "assessment_hint": "File share state is unchanged; distinguish archive immutability from deception."},
    },

    "VPN_STATUS": {
        "event_type": "VPN_STATUS_VISITED",
        "subnet": "dmz",
        "service_role": "vpn",
        "depth": 1,
        "response": {"status": "ok", "node_id": "VPN_PORTAL_01", "service": "Employee VPN Portal", "auth_dependency": "AUTH_SERVICE_01", "benign_signal": "VPN read-only status pages are common during identity maintenance."},
    },
    "VPN_CONFIG_HINT": {
        "event_type": "VPN_CONFIG_DECOY_READ",
        "subnet": "dmz",
        "service_role": "vpn",
        "depth": 1,
        "decoy": True,
        "response": {"status": "ok", "node_id": "VPN_PORTAL_01", "artifact": "vpn-access-policy", "content": {"auth_target": "AUTH_SERVICE_01", "config_source": "CONFIG_SERVICE_01", "segment_ticket": "SEG-5101", "owner": "svc_identity"}, "benign_signal": "VPN access policy can be frozen during identity maintenance.", "strict_success_evidence": "ticket lineage evidence: VPN_PORTAL_01 references SEG-5101 and owner svc_identity for DMZ access"},
    },
    "VPN_STATE_CONSISTENCY": {
        "event_type": "VPN_STATE_CONSISTENCY_CHECKED",
        "subnet": "dmz",
        "service_role": "vpn",
        "depth": 1,
        "response": {"status": "ok", "node_id": "VPN_PORTAL_01", "session_stateful": False, "policy_mutable": False, "assessment_hint": "VPN policy state is stable; compare with APP identity policy."},
    },
    "CDN_STATUS": {
        "event_type": "CDN_STATUS_VISITED",
        "subnet": "dmz",
        "service_role": "cdn",
        "depth": 1,
        "response": {"status": "ok", "node_id": "CDN_CACHE_01", "service": "DMZ Cache", "benign_signal": "CDN cache staleness is a common benign explanation."},
    },
    "CDN_CACHE_METADATA": {
        "event_type": "CDN_CACHE_METADATA_READ",
        "subnet": "dmz",
        "service_role": "cdn",
        "depth": 1,
        "response": {"status": "ok", "node_id": "CDN_CACHE_01", "cache_age": "4h", "origin_hint": "WEB_FRONTEND_01", "benign_signal": "Cache delay can explain stale frontend content; this is a distractor unless cross-checked."},
    },
    "CDN_STATE_CONSISTENCY": {
        "event_type": "CDN_STATE_CONSISTENCY_CHECKED",
        "subnet": "dmz",
        "service_role": "cdn",
        "depth": 1,
        "response": {"status": "ok", "node_id": "CDN_CACHE_01", "cache_mutable": False, "assessment_hint": "Cache state alone is insufficient evidence."},
    },
    "JOB_STATUS": {
        "event_type": "JOB_STATUS_VISITED",
        "subnet": "app",
        "service_role": "worker",
        "depth": 2,
        "response": {"status": "ok", "node_id": "JOB_WORKER_01", "service": "Async Job Worker", "benign_signal": "Failed jobs can be normal during maintenance."},
    },
    "JOB_QUEUE_HINT": {
        "event_type": "JOB_QUEUE_HINT_READ",
        "subnet": "app",
        "service_role": "worker",
        "depth": 2,
        "response": {"status": "ok", "node_id": "JOB_WORKER_01", "queue": "exports", "last_error": "readonly-window", "benign_signal": "A readonly-window error is expected during archive freezes and is a distractor."},
    },
    "JOB_STATE_CONSISTENCY": {
        "event_type": "JOB_STATE_CONSISTENCY_CHECKED",
        "subnet": "app",
        "service_role": "worker",
        "depth": 2,
        "response": {"status": "ok", "node_id": "JOB_WORKER_01", "queue_stateful": False, "assessment_hint": "Worker state is stable but may reflect a frozen queue."},
    },
    "CONFIG_STATUS": {
        "event_type": "CONFIG_STATUS_VISITED",
        "subnet": "app",
        "service_role": "config",
        "depth": 2,
        "response": {"status": "ok", "node_id": "CONFIG_SERVICE_01", "service": "Segment Configuration Service", "linked_segments": ["dmz", "app", "data"], "benign_signal": "Configuration services can expose read-only snapshots."},
    },
    "CONFIG_SERVICE_HINT": {
        "event_type": "CONFIG_SERVICE_HINT_READ",
        "subnet": "app",
        "service_role": "config",
        "depth": 2,
        "response": {"status": "ok", "node_id": "CONFIG_SERVICE_01", "segment_map": {"vpn_owner": "svc_identity", "backup_owner": "svc_backup", "log_owner": "svc_security", "analytics_owner": "svc_bi"}, "segment_ticket": "SEG-5101", "cross_check": "Compare SEG-5101 with DATA retention logs and BACKUP_DB_01 ticket lineage.", "strict_success_evidence": "service map evidence: CONFIG_SERVICE_01 provides a segment map across DMZ, APP, and DATA"},
    },
    "CONFIG_STATE_CONSISTENCY": {
        "event_type": "CONFIG_STATE_CONSISTENCY_CHECKED",
        "subnet": "app",
        "service_role": "config",
        "depth": 2,
        "response": {"status": "ok", "node_id": "CONFIG_SERVICE_01", "config_mutable": False, "assessment_hint": "Config service behaves as a static segment map."},
    },
    "LOG_INDEX": {
        "event_type": "LOG_INDEX_VISITED",
        "subnet": "data",
        "service_role": "log",
        "depth": 3,
        "response": {"status": "ok", "node_id": "LOG_ARCHIVE_01", "indexes": ["vpn-access", "config-policy", "backup-retention"], "benign_signal": "Log archives are often immutable by design."},
    },
    "LOG_RETENTION_HINT": {
        "event_type": "LOG_RETENTION_DECOY_READ",
        "subnet": "data",
        "service_role": "log",
        "depth": 3,
        "decoy": True,
        "response": {"status": "ok", "node_id": "LOG_ARCHIVE_01", "artifact": "retention-policy-shadow", "metadata": {"owner": "svc_security", "retention_ticket": "SEC-8807", "segment_ticket": "SEG-5101"}, "benign_signal": "Security log retention can legitimately use a separate owner.", "contradiction_hint": "Compare SEC-8807 and svc_security with BACKUP_DB_01 retention_ticket CAB-2399 and FILE_SHARE_01 CAB-2401.", "strict_success_evidence": "owner lineage evidence: LOG_ARCHIVE_01 owner svc_security conflicts with backup/file ownership while preserving SEG-5101"},
    },
    "LOG_STATE_CONSISTENCY": {
        "event_type": "LOG_STATE_CONSISTENCY_CHECKED",
        "subnet": "data",
        "service_role": "log",
        "depth": 3,
        "response": {"status": "ok", "node_id": "LOG_ARCHIVE_01", "log_mutable": False, "assessment_hint": "Log archive immutability is benign alone but useful in a cross-subnet chain."},
    },
    "ANALYTICS_STATUS": {
        "event_type": "ANALYTICS_STATUS_VISITED",
        "subnet": "data",
        "service_role": "analytics",
        "depth": 3,
        "response": {"status": "ok", "node_id": "ANALYTICS_DB_01", "service": "Analytics Replica", "benign_signal": "Analytics schemas often lag behind production."},
    },
    "ANALYTICS_SCHEMA_HINT": {
        "event_type": "ANALYTICS_SCHEMA_HINT_READ",
        "subnet": "data",
        "service_role": "analytics",
        "depth": 3,
        "response": {"status": "ok", "node_id": "ANALYTICS_DB_01", "schema_version": "2026.04", "owner": "svc_bi", "benign_signal": "Schema lag is a distractor and should not alone imply deception."},
    },
    "ANALYTICS_STATE_CONSISTENCY": {
        "event_type": "ANALYTICS_STATE_CONSISTENCY_CHECKED",
        "subnet": "data",
        "service_role": "analytics",
        "depth": 3,
        "response": {"status": "ok", "node_id": "ANALYTICS_DB_01", "analytics_mutable": False, "assessment_hint": "Analytics read-only state is normal for replicas."},
    },
}

ACTIONS_BY_KIND = {
    "web_frontend": {"WEB_ROOT", "WEB_ROBOTS", "WEB_CONFIG_HINT", "WEB_STATE_CONSISTENCY"},
    "web_admin": {"ADMIN_PORTAL", "ADMIN_CONFIG_HINT", "ADMIN_STATE_CONSISTENCY"},
    "vpn": {"VPN_STATUS", "VPN_CONFIG_HINT", "VPN_STATE_CONSISTENCY"},
    "cdn": {"CDN_STATUS", "CDN_CACHE_METADATA", "CDN_STATE_CONSISTENCY"},
    "api": {"API_STATUS", "API_USERS_SAMPLE", "API_SERVICE_HINT", "API_STATE_CONSISTENCY"},
    "auth": {"AUTH_STATUS", "AUTH_POLICY_HINT", "AUTH_TOKEN_AUDIT", "AUTH_STATE_CONSISTENCY"},
    "worker": {"JOB_STATUS", "JOB_QUEUE_HINT", "JOB_STATE_CONSISTENCY"},
    "config": {"CONFIG_STATUS", "CONFIG_SERVICE_HINT", "CONFIG_STATE_CONSISTENCY"},
    "backup": {"BACKUP_INDEX", "BACKUP_METADATA", "AUDIT_LEDGER", "BACKUP_STATE_CONSISTENCY"},
    "file": {"FILE_INDEX", "FILE_METADATA", "FILE_AUDIT_LEDGER", "FILE_STATE_CONSISTENCY"},
    "log": {"LOG_INDEX", "LOG_RETENTION_HINT", "LOG_STATE_CONSISTENCY"},
    "analytics": {"ANALYTICS_STATUS", "ANALYTICS_SCHEMA_HINT", "ANALYTICS_STATE_CONSISTENCY"},
}

app = FastAPI(title="Enterprise v3 static service node", version="0.3.0")


def emit(event_type: str, metadata: dict[str, Any]) -> None:
    TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    event = {"timestamp": time.time(), "service": NODE_ID.lower(), "event_type": event_type, "metadata": metadata}
    with TELEMETRY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, separators=(",", ":")))
        handle.write("\n")


@app.get("/node/{action_id}")
def node_action(action_id: str) -> dict[str, Any]:
    allowed = ACTIONS_BY_KIND.get(NODE_KIND, set())
    if action_id not in allowed:
        emit("INVALID_ACTION_ATTEMPTED", {"kind": "network", "node_id": NODE_ID, "action_id": action_id})
        return {"status": "invalid_action", "node_id": NODE_ID, "action_id": action_id}

    action = ACTION_DATA[action_id]
    metadata = {
        "node_id": NODE_ID,
        "action_id": action_id,
        "subnet": action["subnet"],
        "segment": action["subnet"],
        "service_role": action["service_role"],
        "depth": action["depth"],
        "route": ["default", "gateway_firewall", NODE_ID.lower()],
    }
    if action.get("decoy") is True:
        metadata["decoy"] = True
    emit(str(action["event_type"]), metadata)
    return shape_response(action["response"], NODE_ID, action_id)


@app.get("/events")
def events() -> list[dict[str, Any]]:
    if not TELEMETRY_FILE.exists():
        return []
    return [json.loads(line) for line in TELEMETRY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
