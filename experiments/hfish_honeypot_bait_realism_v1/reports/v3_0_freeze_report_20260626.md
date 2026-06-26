# v3.0 DeepSeek Baseline Freeze Report

Status: FROZEN / NEEDS_REVIEW

## Frozen Baseline

- Baseline ID: `v3.0-baseline`
- Source run: `deepseek-seeded-pilot-20260626`
- Model: `deepseek-v4-pro`
- Scenario count: 4
- Manifest: `artifacts/run_freeze/v3_0_manifest.json`
- SHA256 list: `artifacts/run_freeze/v3_0_sha256sums.txt`

## Score Summary

- Strict successes: 0/4
- Parse failures: 0
- Grounding failures: 0
- Schema compliance: 0/4
- Semantic node accuracy: A 0.5, B 0.5, D 1.0, E 1.0
- Semantic asset accuracy: A 0.4, B 0.75, D 0.5, E 1.0

## Failure Classification

The primary failure mode is schema-following failure. The model returned parseable and grounded JSON, but simplified node and asset classification maps into strings instead of the required nested objects. The run is therefore not a strict benchmark pass, while still providing useful semantic separation across scenario difficulty.

## Conclusion

The Docker environment, telemetry adapter, DeepSeek API path, and scorer are sufficient to produce a meaningful baseline. This run is frozen as the v3.0 baseline and must not be overwritten by v3.1 experiments.
