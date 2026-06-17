from honeyagentbench.scenarios import default_v3_seed_plan, generate_v3_scenario


def test_generate_v3_scenario_is_deterministic():
    first = generate_v3_scenario("v3-seed-0001", "easy")
    second = generate_v3_scenario("v3-seed-0001", "easy")

    assert first == second
    assert first.scenario_id.startswith("enterprise-v3-")
    assert first.difficulty == "easy"
    assert first.primary_ticket != first.stale_ticket


def test_default_seed_plan_has_expected_tiers():
    plan = default_v3_seed_plan(10)

    assert len(plan) == 10
    assert [item["difficulty"] for item in plan[:4]] == ["easy"] * 4
    assert [item["difficulty"] for item in plan[4:8]] == ["medium"] * 4
    assert [item["difficulty"] for item in plan[8:]] == ["hard"] * 2
