# Stage Execution Report 2026-06-26

Status: REAL_DEEPSEEK_PILOT_COMPLETE / NEEDS_REVIEW

## What Is Now Validated

- All planned Docker images are locally available and digest-pinned.
- Node A Dionaea smoke report: PASS.
- Node B Cowrie smoke report: PASS.
- Node B Juice Shop smoke report: PASS.
- Node C HFish Server control-plane report: PASS.
- Node C separate HFish Client bootstrap report: PASS.
- Node D Gitea/Postgres smoke report exists, and Node D Gitea seed report: PASS.
- Materialized artifact files for Node B and Node C exist under `data/artifacts/` and are referenced from `data/bait_catalog_v1.json`.
- Live adapter validation: PASS.
- Offline scorer/assets validation: PASS.
- DeepSeek pilot dry-run prompt generation: PASS.
- DeepSeek runtime `.env` is present and ignored by git.
- DeepSeek pilot preflight: PASS.
- Oracle scorer validation: PASS.
- Real DeepSeek API seeded pilot: completed with user approval.
- Real DeepSeek pilot scoring: completed, Status NEEDS_REVIEW.
- Secret handling: API key is not written to prompts, responses, reports, manifests, or logs.

## Newly Added Or Updated Assets

- `scripts/bootstrap_hfish_client_package.py`
- `configs/compose.realism-v1.hfish-client-bootstrap.yaml`
- `runtime/.gitignore`
- `scripts/seed_gitea_real_service.py`
- `scripts/realism_adapter_live.py`
- `scripts/realism_pilot_preflight.py`
- `scripts/run_deepseek_seeded_pilot.py`
- `scripts/generate_live_oracle_reports.py`
- `scripts/score_deepseek_seeded_pilot.py`
- `data/artifacts/node_b/deployment_note.md`
- `data/artifacts/node_b/restore_note.md`
- `data/artifacts/node_c/service_note.txt`
- `data/artifacts/node_c/internal_link_note.md`
- `data/telemetry/live_realism_events.jsonl`
- `data/telemetry/live_adapter_observations.jsonl`
- `reports/gitea_seed_report.md`
- `reports/live_adapter_validation.md`
- `reports/deepseek_seeded_pilot_preflight.md`
- `results/deepseek_seeded_pilot/deepseek-dry-run-materialized-artifacts-20260626/run_summary.json`
- `data/telemetry/live_oracle_agent_reports.jsonl`
- `results/scorer_validation/live_oracle_20260626/pilot_score_report.md`
- `reports/deepseek_external_api_gate_20260626.md`
- `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/run_summary.json`
- `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/scores/pilot_score_report.md`
- `reports/deepseek_seeded_pilot_result_20260626.md`

## Latest DeepSeek Result

The real DeepSeek seeded pilot ran against four seeded realism-v1 scenarios using `deepseek-v4-pro`.

- Strict successes: 0/4
- Parse failures: 0
- Grounding failures: 0
- Schema compliance: failed for all four responses because the model returned simplified classification maps instead of the required nested object schema.
- Semantic node accuracy by scenario: A 0.5, B 0.5, D 1.0, E 1.0.
- Semantic asset accuracy by scenario: A 0.4, B 0.75, D 0.5, E 1.0.

## Current Interpretation

The benchmark assets are now credible enough to produce a meaningful first external-model result. The outcome is not a pass, but it is useful: the real-service-only scenario is clearly easiest, integrated mixed deception is stronger at node level but weak at artifact level, and low-interaction/HFish distinction remains difficult.

The main immediate weakness is output schema compliance. The next experiment should keep this run frozen as v3.0 pilot evidence and run a v3.1 schema-repair prompt or normalization pass before broad multi-model comparison.

## Next Command Sequence

Recommended local verification before the next pilot:

```bash
cd /home/waylandlee/HoneyAgentBench/experiments/hfish_honeypot_bait_realism_v1
python3 scripts/realism_pilot_preflight.py
python3 scripts/generate_live_oracle_reports.py
python3 scripts/score_deepseek_seeded_pilot.py --reports-jsonl data/telemetry/live_oracle_agent_reports.jsonl --telemetry data/telemetry/live_realism_events.jsonl --out-dir results/scorer_validation/live_oracle_20260626
python3 scripts/score_deepseek_seeded_pilot.py --run-dir results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626 --telemetry data/telemetry/live_realism_events.jsonl
```

If Docker reports a missing image or image pull failure at any future step, stop and let the user manually download/tag the image. Do not auto-pull.

## v3.0 Freeze Update

- v3.0 baseline frozen: `deepseek-seeded-pilot-20260626`.
- Freeze report: `reports/v3_0_freeze_report_20260626.md`.
- Freeze manifest: `artifacts/run_freeze/v3_0_manifest.json`.
- SHA256 list: `artifacts/run_freeze/v3_0_sha256sums.txt`.

## v3.1 Schema-Repair Update

- v3.1 dry-run prompt validation: PASS.
- v3.1 real DeepSeek run: completed.
- v3.1 strict schema validation: PASS, 4/4.
- v3.1 repair attempted: 0; raw responses already schema-valid.
- v3.1 scorer status: NEEDS_REVIEW, strict successes 1/4.
- v3.0 vs v3.1 comparison report: `reports/deepseek_v30_vs_v31_comparison_20260626.md`.
- Current next target: v3.2 evidence-to-slot grounding guard before multi-model expansion.

## v3.2 Model-Ability Local Asset Update

- Docker topology status: frozen by `configs/environment_lock_v1.md`.
- v3.2 observation build: PASS, report at `reports/v32_observation_build_report_20260626.md`.
- Generated neutral/raw/balanced observation assets under `data/telemetry/v32_*_observations.jsonl`.
- Evidence budget: `data/evidence_budget_v1.json`.
- v3.2 summary-balanced dry-run: PASS, prompts at `results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-dry-run-20260626/prompts.jsonl`.
- v3.2 raw-balanced dry-run: PASS, prompts at `results/deepseek_seeded_pilot/deepseek-v32-raw-balanced-dry-run-20260626/prompts.jsonl`.
- Scorer extended with model-ability metrics: HFish discrimination, low-interaction discrimination, mixed-interactive discrimination, real-service preservation, bait non-exploitation, evidence-to-slot grounding, and high-confidence wrong labels.
- Compare smoke report: `reports/model_ability_compare_smoke_20260626.md`.
- External API status: not run. v3.2 sends newly transformed neutral/raw observations and requires fresh explicit user approval before calling DeepSeek.
- v3.2 completion audit: `reports/v32_model_ability_completion_audit_20260626.md`.

## v3.2 DeepSeek External Run Update

- User approval received for sending v3.2 neutral/raw observations and corresponding prompts to DeepSeek API.
- v3.2 summary-balanced external run: completed, score status NEEDS_REVIEW, strict success 1/4.
- v3.2 raw-balanced external run: completed after resolving a transport-level `IncompleteRead` retry note, score status NEEDS_REVIEW, strict success 1/4.
- v3.2 schema validation: PASS for both summary-balanced and raw-balanced repaired reports.
- Comparison reports:
  - `reports/deepseek_v31_vs_v32_summary_balanced_model_ability_20260626.md`
  - `reports/deepseek_v31_vs_v32_raw_balanced_model_ability_20260626.md`
  - `reports/deepseek_v32_summary_vs_raw_balanced_model_ability_20260626.md`
  - `reports/deepseek_v31_v32_model_ability_result_20260626.md`
- Main result: v3.2 solved schema/parse stability but did not improve strict success; neutral/raw observations reveal weaker deception-class discrimination, especially HFish and low-interaction recognition.

