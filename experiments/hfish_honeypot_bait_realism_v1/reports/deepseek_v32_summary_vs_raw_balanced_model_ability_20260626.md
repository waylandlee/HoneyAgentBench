# Model Ability Run Comparison

Left: `deepseek-v32-summary-balanced` from `results/deepseek_seeded_pilot/deepseek-v32-summary-balanced-seeded-pilot-20260626/scores/per_scenario_scores.jsonl`
Right: `deepseek-v32-raw-balanced` from `results/deepseek_seeded_pilot/deepseek-v32-raw-balanced-seeded-pilot-20260626/scores/per_scenario_scores.jsonl`

| Metric | Left | Right |
|---|---:|---:|
| scenarios | 4 | 4 |
| strict_success | 1/4 | 1/4 |
| schema_success | 4/4 | 4/4 |
| grounding_success | 2/4 | 3/4 |
| mean_node_accuracy | 0.4375 | 0.375 |
| mean_asset_accuracy | 0.49107142857142855 | 0.5232142857142857 |
| hfish_discrimination_success | 0/3 | 0/3 |
| low_interaction_discrimination_success | 0/2 | 0/2 |
| mixed_interactive_discrimination_success | 0/1 | 0/1 |
| real_service_preservation_success | 3/3 | 3/3 |
| bait_non_exploitation_success | 2/2 | 1/2 |
| evidence_to_slot_grounding_success | 2/4 | 3/4 |
| high_confidence_wrong_count | 8 | 9 |

Interpretation guide:

- If strict/schema improves while ability metrics do not, the change is mainly format or grounding repair.
- If raw-balanced changes ability metrics sharply, the model is sensitive to observation representation.
- If real-service preservation falls, the prompt or evidence mode is over-inducing suspicion.
