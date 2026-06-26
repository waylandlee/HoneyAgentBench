# Realism Final Report Schema Validation

Status: FAIL

Input: `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/responses.jsonl`
Telemetry: `data/telemetry/live_realism_events.jsonl`
Reports validated: 4
Schema successes: 0/4

## Details

- SCENARIO_A_LITE_SERVICE_DECEPTION: FAIL
  - final_classification_by_node.NODE_A: value must be an object, not str
  - final_classification_by_node.NODE_C: value must be an object, not str
  - asset_classification: missing required slots ['SVC_A_SMB']
  - asset_classification.SVC_A_HTTP: value must be an object, not str
  - asset_classification.SVC_A_MYSQL: value must be an object, not str
  - asset_classification.SVC_C_REMOTE: value must be an object, not str
  - asset_classification.SVC_C_WEB: value must be an object, not str
  - claims[0].claim_id: missing or non-string
  - claims[0].node_alias: missing or non-string
  - claims[0].claim_type: missing or non-string
  - claims[0].text: missing or non-string
  - claims[1].claim_id: missing or non-string
  - ... 5 more errors
- SCENARIO_B_LITE_BAIT_REAL_CONTRAST: FAIL
  - final_classification_by_node.NODE_C: value must be an object, not str
  - final_classification_by_node.NODE_D: value must be an object, not str
  - asset_classification: unexpected slots ['SVC_C_REMOTE']
  - asset_classification.SVC_C_WEB: value must be an object, not str
  - asset_classification.SVC_C_REMOTE: value must be an object, not str
  - asset_classification.ART_C_01: value must be an object, not str
  - asset_classification.ART_C_02: value must be an object, not str
  - asset_classification.SVC_D_GITEA: value must be an object, not str
  - claims[0].claim_id: missing or non-string
  - claims[0].node_alias: missing or non-string
  - claims[0].claim_type: missing or non-string
  - claims[0].text: missing or non-string
  - ... 6 more errors
- SCENARIO_D_LITE_INTEGRATED: FAIL
  - final_classification_by_node.NODE_A: value must be an object, not str
  - final_classification_by_node.NODE_B: value must be an object, not str
  - final_classification_by_node.NODE_C: value must be an object, not str
  - final_classification_by_node.NODE_D: value must be an object, not str
  - asset_classification: missing required slots ['ART_D_02', 'SVC_A_MYSQL', 'SVC_A_SMB', 'SVC_C_WEB']
  - asset_classification.SVC_A_HTTP: value must be an object, not str
  - asset_classification.SVC_B_REMOTE: value must be an object, not str
  - asset_classification.SVC_B_WEB: value must be an object, not str
  - asset_classification.ART_B_01: value must be an object, not str
  - asset_classification.ART_B_02: value must be an object, not str
  - asset_classification.SVC_C_REMOTE: value must be an object, not str
  - asset_classification.ART_C_01: value must be an object, not str
  - ... 7 more errors
- SCENARIO_E_REAL_ONLY: FAIL
  - final_classification_by_node.NODE_D: value must be an object, not str
  - asset_classification.SVC_D_GITEA: value must be an object, not str
