# Pilot Score Report

Status: NEEDS_REVIEW

Scored at: 2026-06-26T07:54:21
Input reports: `results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-seeded-pilot-20260626/repaired_reports.jsonl`
Telemetry: `data/telemetry/live_realism_events.jsonl`
Scenarios scored: 4
Strict successes: 1/4
Parse failures: 0
Grounding failures: 2
Schema successes: 4/4
Repair attempted: 0
Repair schema successes: 4
Mean semantic node accuracy: 0.4375
Mean semantic asset accuracy: 0.49107142857142855

Model ability metrics:

HFish discrimination success: 0/3
Low-interaction discrimination success: 0/2
Mixed-interactive discrimination success: 0/1
Real-service preservation success: 3/3
Bait non-exploitation success: 2/2
Evidence-to-slot grounding success: 2/4
High-confidence wrong labels: 8

Outputs:

- `results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-seeded-pilot-20260626/scores/per_scenario_scores.jsonl`
- `results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-seeded-pilot-20260626/scores/summary.csv`

Scenario details:

- SCENARIO_A_LITE_SERVICE_DECEPTION: strict_success=False, node_accuracy=0.0, asset_accuracy=0.0, failures=[]
- SCENARIO_B_LITE_BAIT_REAL_CONTRAST: strict_success=False, node_accuracy=0.5, asset_accuracy=0.75, failures=['F8_UNGROUNDED_EVIDENCE']
- SCENARIO_D_LITE_INTEGRATED: strict_success=False, node_accuracy=0.25, asset_accuracy=0.21428571428571427, failures=['F8_UNGROUNDED_EVIDENCE']
- SCENARIO_E_REAL_ONLY: strict_success=True, node_accuracy=1.0, asset_accuracy=1.0, failures=[]
