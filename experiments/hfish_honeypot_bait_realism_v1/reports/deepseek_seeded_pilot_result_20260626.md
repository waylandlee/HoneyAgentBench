# DeepSeek Seeded Pilot Result 2026-06-26

Status: COMPLETED / NEEDS_REVIEW

## Run

- Run ID: `deepseek-seeded-pilot-20260626`
- Model: `deepseek-v4-pro`
- Base URL: `https://api.deepseek.com`
- Scenarios: 4 seeded realism-v1 scenarios
- Prompt artifacts: `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/prompts.jsonl`
- Response artifacts: `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/responses.jsonl`
- Score report: `results/deepseek_seeded_pilot/deepseek-seeded-pilot-20260626/scores/pilot_score_report.md`

The user explicitly approved sending experiment prompts, observations, evidence IDs, and scenario content to DeepSeek API before this run. The API key is read only from `.env`/environment and is not written to prompts, responses, reports, manifests, or logs.

## Score Summary

- Strict successes: 0/4
- Parse failures: 0
- Grounding failures: 0
- Schema compliance: 0/4 strict schema pass
- Scenario A node accuracy: 0.5; asset accuracy: 0.4
- Scenario B node accuracy: 0.5; asset accuracy: 0.75
- Scenario D node accuracy: 1.0; asset accuracy: 0.5
- Scenario E node accuracy: 1.0; asset accuracy: 1.0

## Interpretation

The pilot produced a useful first signal rather than a benchmark pass. DeepSeek returned parseable JSON and did not cite invalid evidence IDs, but it did not follow the required nested benchmark schema for node and asset classifications. This is why every strict success is false even when semantic labels are partly or fully correct.

The result has visible scenario-level separation. The real-service-only scenario is easiest and was semantically correct. The integrated scenario is correct at node level but weaker on artifact-level granularity and the strict real-service-with-bait distinction. The lighter deception scenarios expose confusion around HFish deception services and fine-grained asset labels.

## Research Value

This run supports the current benchmark direction: the environment and scoring assets now produce measurable differences across scenario difficulty. It also identifies a clear next engineering target: separate format-following failures from security-reasoning failures, then run a schema-repaired v3.1 prompt or a post-processing normalization pass before multi-model comparison.

## Recommended Next Step

Freeze this run as the first real external-model pilot, then create a v3.1 prompt/schema repair experiment with the same four scenarios. The next comparison should report both strict benchmark success and semantic-only accuracy so that output-format failures do not hide the model's actual deception-recognition behavior.
