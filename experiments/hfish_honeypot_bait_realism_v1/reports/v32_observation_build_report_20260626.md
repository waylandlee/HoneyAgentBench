# v3.2 Model-Ability Observation Build Report

Status: PASS

Generated at: 2026-06-26T07:40:22
Source observations: `data/telemetry/live_adapter_observations.jsonl`
Source events: `data/telemetry/live_realism_events.jsonl`

Generated files:

- `data/telemetry/v32_neutral_summary_observations.jsonl`: 39 rows
- `data/telemetry/v32_raw_interaction_observations.jsonl`: 39 rows
- `data/telemetry/v32_raw_full_observations.jsonl`: 39 rows
- `data/telemetry/v32_summary_balanced_observations.jsonl`: 32 rows
- `data/telemetry/v32_raw_balanced_observations.jsonl`: 32 rows
- `data/evidence_budget_v1.json`: balanced evidence policy and selected evidence IDs

Validation checks:

- Rewrites exist for every source action.
- Model-facing observation text excludes configured ground-truth/framing terms.
- Evidence IDs remain stable so the existing scorer can verify grounding against live telemetry.
- Balanced views cap evidence volume per scenario/node/role without changing Docker topology.

No validation issues found.
