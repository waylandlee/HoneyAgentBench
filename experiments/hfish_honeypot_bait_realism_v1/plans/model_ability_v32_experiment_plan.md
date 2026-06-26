# v3.2 Model-Ability Experiment Plan

Status: IMPLEMENTED_LOCALLY_PENDING_EXTERNAL_RUN_APPROVAL

Date: 2026-06-26 Asia/Shanghai

## Research Goal

Measure model reasoning ability under the existing HoneyAgentBench realism-v1 Docker lab. v3.2 asks whether the model can distinguish low-depth services, HFish-style node behavior, mixed interactive nodes, real services, and suspicious file notes when the observation text is less leading and evidence volume is balanced.

## Design Principle

Docker is held constant. The experiment changes only what the model sees:

- v3.1: schema-repaired summary observations.
- v3.2 neutral-summary: less leading summary observations.
- v3.2 summary-balanced: neutral summary observations with capped evidence volume.
- v3.2 raw-balanced: raw-style protocol/page/file observations with capped evidence volume.
- v3.2 raw-full: raw-style fixed-action observations without balancing.

## Implemented Assets

- `configs/environment_lock_v1.md`
- `scripts/build_v32_model_ability_observations.py`
- `scripts/run_deepseek_seeded_pilot_v32.py`
- `data/evidence_budget_v1.json`
- `data/telemetry/v32_neutral_summary_observations.jsonl`
- `data/telemetry/v32_summary_balanced_observations.jsonl`
- `data/telemetry/v32_raw_interaction_observations.jsonl`
- `data/telemetry/v32_raw_full_observations.jsonl`
- `data/telemetry/v32_raw_balanced_observations.jsonl`
- `reports/v32_observation_build_report_20260626.md`
- `results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-dry-run-20260626/prompts.jsonl`
- `results/deepseek_seeded_pilot/deepseek-v32-raw-balanced-dry-run-20260626/prompts.jsonl`

## Local Execution Sequence

```bash
cd /home/waylandlee/HoneyAgentBench/experiments/hfish_honeypot_bait_realism_v1
python3 scripts/build_v32_model_ability_observations.py
python3 scripts/run_deepseek_seeded_pilot_v32.py --dry-run --observation-mode summary_balanced --run-id deepseek-v32-summary-balanced-dry-run-20260626 --overwrite
python3 scripts/run_deepseek_seeded_pilot_v32.py --dry-run --observation-mode raw_balanced --run-id deepseek-v32-raw-balanced-dry-run-20260626 --overwrite
```

## External API Gate

Do not run the v3.2 DeepSeek API experiment until the user explicitly approves sending the new v3.2 neutral/raw observations. The v3.2 runner enforces this by refusing non-dry-run execution unless `--confirm-external-upload-v32` is supplied.

Recommended run IDs after approval:

```bash
python3 scripts/run_deepseek_seeded_pilot_v32.py --observation-mode summary_balanced --run-id deepseek-v32-summary-balanced-seeded-pilot-20260626 --confirm-external-upload-v32
python3 scripts/run_deepseek_seeded_pilot_v32.py --observation-mode raw_balanced --run-id deepseek-v32-raw-balanced-seeded-pilot-20260626 --confirm-external-upload-v32
```

Then score each run:

```bash
python3 scripts/score_deepseek_seeded_pilot.py --run-dir results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-seeded-pilot-20260626 --telemetry data/telemetry/live_realism_events.jsonl
python3 scripts/score_deepseek_seeded_pilot.py --run-dir results/deepseek_seeded_pilot/deepseek-v32-raw-balanced-seeded-pilot-20260626 --telemetry data/telemetry/live_realism_events.jsonl
```

## Primary v3.2 Questions

- Does neutral wording reduce observation-framing bias?
- Does raw evidence improve or harm HFish discrimination?
- Does balanced evidence reduce over-attention to file notes?
- Does the model preserve real-service classification when suspicious-looking files exist?
- Does the model cite evidence IDs in the correct node/asset slot?
- Are wrong labels high-confidence or appropriately uncertain?

## Acceptance Gate For v3.2 Local Assets

- Observation build report PASS.
- Prompt dry-run report PASS for `summary_balanced` and `raw_balanced`.
- Scorer still passes oracle reports.
- Scorer still handles v3.1 repaired reports.
- Secret scan passes.
- Docker final check shows no experiment containers running.
