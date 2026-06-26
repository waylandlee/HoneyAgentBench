# Model Ability Run Comparison

Left: `deepseek-v31` from `results/deepseek_seeded_pilot/deepseek-v31-seeded-pilot-20260626/scores/per_scenario_scores.jsonl`
Right: `deepseek-v32-summary-balanced` from `results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-seeded-pilot-20260626/scores/per_scenario_scores.jsonl`

| Metric | Left | Right |
|---|---:|---:|
| scenarios | 4 | 4 |
| strict_success | 1/4 | 1/4 |
| schema_success | 4/4 | 4/4 |
| grounding_success | 2/4 | 2/4 |
| mean_node_accuracy | 0.75 | 0.4375 |
| mean_asset_accuracy | 0.6678571428571428 | 0.49107142857142855 |
| hfish_discrimination_success | 1/3 | 0/3 |
| low_interaction_discrimination_success | 2/2 | 0/2 |
| mixed_interactive_discrimination_success | 1/1 | 0/1 |
| real_service_preservation_success | 3/3 | 3/3 |
| bait_non_exploitation_success | 2/2 | 2/2 |
| evidence_to_slot_grounding_success | 2/4 | 2/4 |
| high_confidence_wrong_count | 8 | 8 |

Interpretation guide:

- If strict/schema improves while ability metrics do not, the change is mainly format or grounding repair.
- If raw-balanced changes ability metrics sharply, the model is sensitive to observation representation.
- If real-service preservation falls, the prompt or evidence mode is over-inducing suspicion.
