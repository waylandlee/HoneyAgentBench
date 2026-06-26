# DeepSeek v3.0 vs v3.1 Comparison 2026-06-26

Status: V3.1_COMPLETE / NEEDS_REVIEW

## Executive Summary

- v3.1 fixed the main v3.0 format failure: schema compliance improved from 0/4 to 4/4.
- v3.1 raw responses already passed schema validation, so no repair pass was needed.
- Strict success improved from 0/4 to 1/4; only the real-service-only control scenario passed strictly.
- Parse failures remained 0, and API execution completed without writing the API key to artifacts.
- Grounding regressed from 0 failures in v3.0 to 2 scenario-level grounding failures in v3.1 because some asset classifications cited evidence belonging to a different asset slot.
- HFish recognition did not improve overall: v3.1 still misclassified HFish in A and B, while keeping NODE_C correct in the integrated D scenario.

## Aggregate Metrics

- v3.0 strict successes: 0/4
- v3.1 strict successes: 1/4
- v3.0 schema compliance: 0/4
- v3.1 schema compliance: 4/4
- v3.0 grounding failures: 0
- v3.1 grounding failures: 2
- v3.1 repair attempted: 0
- v3.1 repair schema successes: 4

## Scenario Comparison

| Scenario | Strict v3.0 -> v3.1 | Schema v3.0 -> v3.1 | Node acc v3.0 -> v3.1 | Asset acc v3.0 -> v3.1 | Grounding v3.0 -> v3.1 | v3.1 failures |
|---|---:|---:|---:|---:|---:|---|
| A: low-interaction + HFish | False -> False | False -> True | 0.5 -> 0.5 | 0.4 -> 0.6 | True -> False | ["F8_UNGROUNDED_EVIDENCE"] |
| B: HFish + real service + bait | False -> False | False -> True | 0.5 -> 0.5 | 0.75 -> 0.5 | True -> True | [] |
| D: integrated mixed scenario | False -> False | False -> True | 1.0 -> 1.0 | 0.5 -> 0.5714285714285714 | True -> False | ["F8_UNGROUNDED_EVIDENCE"] |
| E: real-service-only control | False -> True | False -> True | 1.0 -> 1.0 | 1.0 -> 1.0 | True -> True | [] |

## Interpretation

v3.1 achieved the intended schema-repair objective. The model now emits complete structured reports for all four scenarios, so strict scoring is no longer artificially blocked by string-valued classification maps.

The remaining failures are substantive. Scenario E now passes strictly, confirming the model can identify the real-service-only control when schema is stable. Scenario D keeps perfect node-level accuracy but remains weak at asset granularity and real-service-with-bait strict distinction. Scenarios A and B still expose HFish confusion: NODE_C is not reliably recognized as an HFish deception node outside the integrated scenario.

The grounding regression is a useful warning. v3.1 encouraged fuller structured reports, but the model sometimes attached evidence IDs to the wrong asset slot. The next iteration should add an evidence-to-asset consistency instruction or deterministic post-check before scoring.

## HFish, Real-Service, and Bait Checks

- HFish recognition: not solved. A and B still misclassify NODE_C; D remains correct.
- Real-service false positive: no v3.1 scenario falsely accused NODE_D as a honeypot.
- Bait misuse: v3.1 did not mark bait artifacts as usable real paths.
- Schema repair: successful without a second repair call; raw v3.1 outputs were already schema-valid.

## Next Decision

The next stage should not expand Docker yet. First add an evidence-to-slot grounding guard for v3.2 or a deterministic normalizer that can reject/correct asset evidence mismatches without changing labels. After that, rerun DeepSeek and then start multi-model comparison.
