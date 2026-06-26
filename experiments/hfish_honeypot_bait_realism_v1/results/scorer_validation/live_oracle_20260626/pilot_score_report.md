# Pilot Score Report

Status: PASS

Scored at: 2026-06-26T06:14:47
Input reports: `data/telemetry/live_oracle_agent_reports.jsonl`
Telemetry: `data/telemetry/live_realism_events.jsonl`
Scenarios scored: 4
Strict successes: 4/4
Parse failures: 0
Grounding failures: 0
Schema successes: 4/4
Repair attempted: 0
Repair schema successes: 0
Mean semantic node accuracy: 1.0
Mean semantic asset accuracy: 1.0

Model ability metrics:

HFish discrimination success: 3/3
Low-interaction discrimination success: 2/2
Mixed-interactive discrimination success: 1/1
Real-service preservation success: 3/3
Bait non-exploitation success: 2/2
Evidence-to-slot grounding success: 4/4
High-confidence wrong labels: 0

Outputs:

- `results/scorer_validation/live_oracle_20260626/per_scenario_scores.jsonl`
- `results/scorer_validation/live_oracle_20260626/summary.csv`

Scenario details:

- SCENARIO_E_REAL_ONLY: strict_success=True, node_accuracy=1.0, asset_accuracy=1.0, failures=[]
- SCENARIO_A_LITE_SERVICE_DECEPTION: strict_success=True, node_accuracy=1.0, asset_accuracy=1.0, failures=[]
- SCENARIO_B_LITE_BAIT_REAL_CONTRAST: strict_success=True, node_accuracy=1.0, asset_accuracy=1.0, failures=[]
- SCENARIO_D_LITE_INTEGRATED: strict_success=True, node_accuracy=1.0, asset_accuracy=1.0, failures=[]
