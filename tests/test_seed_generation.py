import yaml

from honeyagentbench.scenarios import generate_v3_scenario
from scripts.generate_v3_scenarios import generate_one


def test_generate_one_seeded_eval_reuses_v3_images_and_pins_seed(tmp_path):
    scenario = generate_v3_scenario("v3-seed-9999", "hard").asdict()

    target = generate_one(tmp_path, scenario, "benchmark", force=False)

    eval_data = yaml.safe_load((target / "eval.yaml").read_text(encoding="utf-8"))
    compose = yaml.safe_load((target / "sandbox_configs" / "compose.yaml").read_text(encoding="utf-8"))

    assert eval_data["metadata"]["scenario_seed"] == "v3-seed-9999"
    assert eval_data["metadata"]["scenario_difficulty"] == "hard"
    assert compose["services"]["gateway_firewall"]["environment"]["HAB_RESPONSE_MODE"] == "benchmark"
    assert compose["services"]["gateway_firewall"]["build"]["context"].endswith("multinode_enterprise_v3/images/gateway_firewall")
