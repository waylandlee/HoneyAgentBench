# DeepSeek Seeded Pilot Preflight

Status: PASS

Scope: local readiness gate only. This script does not call DeepSeek or any external API.

Completed checks:

- All planned non-adapter images have pinned digests.
- reports/node_a_dionaea_smoke_report.md contains `Status: PASS`.
- reports/node_b_cowrie_smoke_report.md contains `Status: PASS`.
- reports/node_b_juice_smoke_report.md contains `Status: PASS`.
- reports/node_c_hfish_client_smoke_report.md contains `Status: PASS`.
- reports/hfish_server_smoke_report.md contains `Status: PASS`.
- reports/offline_scorer_validation.md contains `Status: PASS`.
- reports/live_adapter_validation.md contains `Status: PASS`.
- results/scorer_validation/live_oracle_20260626/pilot_score_report.md contains `Status: PASS`.
- Live adapter produced 39 evidence events and 39 observations.
- DEEPSEEK_API_KEY is available to runtime without being printed.

Next action:

- Resolve blockers before running `scripts/run_deepseek_seeded_pilot.py` without `--dry-run`.
- If Docker reports a missing image or pull failure, stop and let the user manually download/tag the image.
