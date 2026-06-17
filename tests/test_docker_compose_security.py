from pathlib import Path

import yaml


def load_compose(path: str):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def assert_restricted_service(service):
    assert service.get("read_only") is True
    assert "ALL" in service.get("cap_drop", [])
    assert "no-new-privileges:true" in service.get("security_opt", [])
    assert "/tmp" in service.get("tmpfs", [])


def test_enterprise_v3_compose_keeps_internal_networks_and_restricted_containers():
    compose = load_compose("evals/multinode_enterprise_v3/sandbox_configs/compose.yaml")

    assert compose["networks"]["edge_net"]["internal"] is True
    assert compose["networks"]["service_net"]["internal"] is True
    for service in compose["services"].values():
        assert_restricted_service(service)


def test_static_baseline_pins_debug_response_mode():
    compose = load_compose("evals/multinode_enterprise_v3_static_baseline/sandbox_configs/compose.yaml")

    assert compose["services"]["gateway_firewall"]["environment"]["HAB_SCENARIO_SEED"] == "v3-static-baseline"
    assert compose["services"]["gateway_firewall"]["environment"]["HAB_RESPONSE_MODE"] == "debug"
