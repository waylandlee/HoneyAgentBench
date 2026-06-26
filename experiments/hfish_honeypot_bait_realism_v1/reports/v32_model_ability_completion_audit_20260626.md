# v3.2 Model-Ability Completion Audit

Status: COMPLETE_NEEDS_REVIEW

Generated at: 2026-06-26 06:20:20 Asia/Shanghai

## Objective Under Audit

Execute the adjusted staged plan for measuring model ability rather than Docker deployment variability.

The current v3.2 scope is: freeze Docker, transform model-visible observations, balance evidence, add raw/neutral prompt modes, extend scoring metrics, validate locally, and stop before any external API call unless the user explicitly approves sending the new v3.2 neutral/raw observations.

## Requirement Evidence Matrix

| Requirement | Status | Evidence |
|---|---|---|
| Freeze Docker topology | COMPLETE | `configs/environment_lock_v1.md` states no topology/image/node/scenario changes for v3.2. |
| Preserve v3.0/v3.1 assets | COMPLETE | v3.2 writes new `v32_*` telemetry and new dry-run directories; v3.0/v3.1 prompts/responses are not overwritten. |
| Build neutral summary observations | COMPLETE | `data/telemetry/v32_neutral_summary_observations.jsonl`, 39 rows. |
| Build raw interaction observations | COMPLETE | `data/telemetry/v32_raw_interaction_observations.jsonl`, 39 rows. |
| Build balanced evidence views | COMPLETE | `data/telemetry/v32_summary_balanced_observations.jsonl` and `data/telemetry/v32_raw_balanced_observations.jsonl`, 32 rows each. |
| Record evidence budget | COMPLETE | `data/evidence_budget_v1.json`. |
| Validate observation rewrites | COMPLETE | `reports/v32_observation_build_report_20260626.md`, Status PASS. |
| Add v3.2 dry-run runner | COMPLETE | `scripts/run_deepseek_seeded_pilot_v32.py`. |
| Generate summary-balanced prompts | COMPLETE | `results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-dry-run-20260626/prompts.jsonl`; run summary reports `dry_run=true`, `prompt_validation_pass=true`, `external_upload_status=not_performed`. |
| Generate raw-balanced prompts | COMPLETE | `results/deepseek_seeded_pilot/deepseek-v32-raw-balanced-dry-run-20260626/prompts.jsonl`; run summary reports `dry_run=true`, `prompt_validation_pass=true`, `external_upload_status=not_performed`. |
| Prevent accidental v3.2 external upload | COMPLETE | Runner requires `--confirm-external-upload-v32` for non-dry-run v3.2 execution. Gate test returned nonzero and created no output directory. |
| Extend scorer with model-ability metrics | COMPLETE | `scripts/score_deepseek_seeded_pilot.py` reports HFish discrimination, low-interaction discrimination, mixed-interactive discrimination, real-service preservation, bait non-exploitation, evidence-to-slot grounding, and high-confidence wrong labels. |
| Add comparison utility | COMPLETE | `scripts/compare_model_ability_runs.py`; smoke report `reports/model_ability_compare_smoke_20260626.md`. |
| Update metric documentation | COMPLETE | `plans/metric_definitions_v1.md` includes `## v3.2 Model-Ability Metrics`. |
| Update artifact manifest | COMPLETE | `configs/image_manifest_v1.lock` status is `v32-external-runs-complete-needs-review`. |
| Run local verification | COMPLETE | py_compile, preflight, asset validation, oracle schema/scorer, v3.1 scorer, v3.2 dry-runs all passed or matched expected NEEDS_REVIEW for v3.1 semantic score. |
| Secret scan | COMPLETE | Secret scan over experiment assets excluding `.env` and `runtime/` returned PASS. |
| Docker final check | COMPLETE | `docker ps --format` returned no running experiment containers. |
| Run v3.2 DeepSeek API experiment | COMPLETE | User approval received; summary-balanced and raw-balanced DeepSeek external runs completed and scored. |

## External Run Status

The v3.2 external DeepSeek runs are complete. The runner still keeps the `--confirm-external-upload-v32` gate for any future rerun so newly transformed observations are not uploaded accidentally.

## Audit Conclusion

The adjusted v3.2 staged plan has been executed end to end. The final research status is `COMPLETE_NEEDS_REVIEW`: engineering, prompting, external runs, schema validation, scoring, comparison reports, secret scan, and Docker final checks are complete; the results themselves indicate semantic weaknesses that should be addressed in a next v3.3 calibration stage.

## External Run Completion Addendum

- Approval for v3.2 neutral/raw observation upload was received in the Codex thread.
- `deepseek-v32-summary-balanced-seeded-pilot-20260626` completed and scored.
- `deepseek-v32-raw-balanced-seeded-pilot-20260626` completed and scored after a documented transport retry.
- Both v3.2 repaired report files passed schema validation.
- Final result status is NEEDS_REVIEW because strict success remains 1/4 for both v3.2 modes.
