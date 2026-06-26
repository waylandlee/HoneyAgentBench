# DeepSeek External API Gate 2026-06-26

Status: APPROVED_AND_COMPLETED

## Approval Record

The user explicitly approved sending experiment prompts, observations, evidence IDs, and scenario content to DeepSeek API for this seeded pilot.

## What Passed Before The Run

- Local `.env` exists and is ignored by git.
- `scripts/realism_pilot_preflight.py` returns PASS.
- DeepSeek model selection is configured as `deepseek-v4-pro` with base URL `https://api.deepseek.com`.
- Prompt dry-run generation works.
- Scorer validation against live oracle reports returns PASS.

## Completed API Run

```bash
cd /home/waylandlee/HoneyAgentBench/experiments/hfish_honeypot_bait_realism_v1
python3 scripts/run_deepseek_seeded_pilot.py --run-id deepseek-seeded-pilot-20260626
python3 scripts/score_deepseek_seeded_pilot.py --run-dir results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626 --telemetry data/telemetry/live_realism_events.jsonl
```

## Output Locations

- `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/run_summary.json`
- `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/prompts.jsonl`
- `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/responses.jsonl`
- `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/scores/pilot_score_report.md`
- `reports/deepseek_seeded_pilot_result_20260626.md`

## Result

The run completed without parse failures or grounding failures, but the final benchmark status is NEEDS_REVIEW because the model did not follow the strict nested output schema and therefore had 0/4 strict successes.

No API key is written into reports, logs, prompts, manifests, or committed artifacts.
