from pathlib import Path

from honeyagentbench.constants import DEFAULT_SYSTEM_MESSAGE, MULTINODE_ACTIONS_BY_NODE, MULTINODE_ACTION_IDS, MULTINODE_NODE_IDS, SSH_COMMAND_IDS, WEB_PATH_IDS


def test_ssh_command_ids_do_not_include_dangerous_actions():
    joined = " ".join(SSH_COMMAND_IDS).lower()

    for forbidden in ["shell", "exec", "payload", "scan", "nmap", "sqlmap", "metasploit", "curl", "wget"]:
        assert forbidden not in joined


def test_web_path_ids_are_not_urls_or_raw_paths():
    for path_id in WEB_PATH_IDS:
        assert "://" not in path_id
        assert "/" not in path_id
        assert path_id == path_id.upper()


def test_allowed_id_sets_are_non_empty_and_unique():
    assert len(SSH_COMMAND_IDS) == len(set(SSH_COMMAND_IDS))
    assert len(WEB_PATH_IDS) == len(set(WEB_PATH_IDS))
    assert SSH_COMMAND_IDS
    assert WEB_PATH_IDS


def test_multinode_ids_are_safe_enums():
    forbidden = ["://", "/", ".", " ", "shell", "exec", "payload", "scan", "nmap", "curl", "wget"]
    for node_id in MULTINODE_NODE_IDS:
        assert node_id == node_id.upper()
        for item in forbidden:
            assert item not in node_id.lower()
    for action_id in MULTINODE_ACTION_IDS:
        assert action_id == action_id.upper()
        for item in forbidden:
            assert item not in action_id.lower()


def test_multinode_action_mapping_is_complete_and_unique():
    assert set(MULTINODE_ACTIONS_BY_NODE) == set(MULTINODE_NODE_IDS)
    assert len(MULTINODE_ACTION_IDS) == len(set(MULTINODE_ACTION_IDS))
    for actions in MULTINODE_ACTIONS_BY_NODE.values():
        assert actions


def test_multinode_backup_public_action_uses_audit_ledger_name():
    assert "AUDIT_LEDGER" in MULTINODE_ACTION_IDS
    assert "CANARY_RECORD" not in MULTINODE_ACTION_IDS



def test_enterprise_v2_nodes_and_actions_are_available():
    assert {"WEB_ADMIN_01", "AUTH_SERVICE_01", "FILE_SHARE_01"}.issubset(MULTINODE_NODE_IDS)
    assert {"ADMIN_PORTAL", "AUTH_TOKEN_AUDIT", "FILE_AUDIT_LEDGER"}.issubset(MULTINODE_ACTION_IDS)


def test_enterprise_v2_prompt_contains_strict_success_guidance():
    prompt_text = Path("evals/multinode_enterprise_v2/eval.yaml").read_text(encoding="utf-8").lower()

    for required in [
        "strict success evidence checklist",
        "service map evidence",
        "route consistency evidence",
        "ticket lineage evidence",
        "owner lineage evidence",
        "efficient strict path",
        "api_service_hint",
        "within 16 network_interact calls",
        "gateway -> dmz -> app -> data",
        "each service node should receive at most one network_interact call",
        "do not return to an earlier subnet",
        "do not backtrack to dmz or app after entering data",
    ]:
        assert required in prompt_text


def test_enterprise_v2_service_feedback_contains_strict_success_labels():
    service_text = Path("evals/multinode_enterprise_v2/images/service_node/app.py").read_text(encoding="utf-8").lower()
    gateway_text = Path("evals/multinode_enterprise_v2/images/gateway_firewall/app.py").read_text(encoding="utf-8").lower()
    joined = service_text + "\n" + gateway_text

    for required in [
        "strict_success_evidence",
        "service map evidence",
        "route consistency evidence",
        "ticket lineage evidence",
        "owner lineage evidence",
        "cross-node contradiction",
        "path_planning_constraint",
        "strict_path_order",
        "recommended_one_pass_actions",
        "gateway -> dmz -> app -> data",
        "each service node should be queried at most once",
    ]:
        assert required in joined



def test_enterprise_v3_nodes_actions_and_prompt_are_available():
    expected_nodes = {
        "VPN_PORTAL_01",
        "CDN_CACHE_01",
        "JOB_WORKER_01",
        "CONFIG_SERVICE_01",
        "LOG_ARCHIVE_01",
        "ANALYTICS_DB_01",
    }
    expected_actions = {
        "CHECK_SEGMENT_POLICY",
        "VPN_CONFIG_HINT",
        "CDN_CACHE_METADATA",
        "JOB_QUEUE_HINT",
        "CONFIG_SERVICE_HINT",
        "LOG_RETENTION_HINT",
        "ANALYTICS_SCHEMA_HINT",
    }
    assert expected_nodes.issubset(MULTINODE_NODE_IDS)
    assert expected_actions.issubset(MULTINODE_ACTION_IDS)

    prompt_text = Path("evals/multinode_enterprise_v3/eval.yaml").read_text(encoding="utf-8").lower()
    for required in [
        "multinode-enterprise-v3",
        "three logical subnets",
        "critical evidence nodes",
        "distractor nodes",
        "minimal critical path within 14 network_interact calls",
        "22-call hard budget",
        "route consistency evidence",
        "service map evidence",
        "ticket lineage evidence",
        "owner lineage evidence",
        "cross-node contradiction",
        "minimal critical action map",
        "web_admin_01/admin_config_hint",
        "vpn_portal_01/vpn_config_hint",
        "config_service_01/config_service_hint",
        "log_archive_01/log_retention_hint",
        "generic check_state_consistency",
        "web_root",
        "cdn_state_consistency",
    ]:
        assert required in prompt_text


def test_enterprise_v3_system_message_blocks_singlehop_aliases():
    system_text = DEFAULT_SYSTEM_MESSAGE.lower()

    for required in [
        "minimal critical action map",
        "gateway_fw_01/map_topology",
        "web_admin_01/admin_config_hint",
        "root, login, robots, admin, backup",
        "generic check_state_consistency",
        "web_state_consistency",
        "analytics_state_consistency",
    ]:
        assert required in system_text


def test_enterprise_v3_feedback_contains_critical_path_labels():
    service_text = Path("evals/multinode_enterprise_v3/images/service_node/app.py").read_text(encoding="utf-8").lower()
    gateway_text = Path("evals/multinode_enterprise_v3/images/gateway_firewall/app.py").read_text(encoding="utf-8").lower()
    joined = service_text + "\n" + gateway_text

    for required in [
        "critical_path_evidence",
        "critical_nodes",
        "distractor_nodes",
        "recommended_minimal_actions",
        "segment policy evidence",
        "service map evidence",
        "ticket lineage evidence",
        "owner lineage evidence",
        "cross-node contradiction",
        "benign_signal",
    ]:
        assert required in joined
