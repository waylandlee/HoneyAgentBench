# ?? Enterprise v3 Seeded Scenarios

? runbook ??????? seeded enterprise v3 ???

## ????

```bash
python scripts/generate_v3_scenarios.py --count 10 --response-mode benchmark --force
```

???????

```text
evals/multinode_enterprise_v3_seed_0001/
evals/multinode_enterprise_v3_seed_0002/
```

?? manifest?

```text
evals/multinode_enterprise_v3_seed_manifest.json
```

## ???? seed

```bash
bash scripts/run_deepseek.sh deepseek-v4-pro multinode-enterprise-v3-seed-0001 baseline-react
```

## ????

- ??? seed?????
- ??? `benchmark` response mode?
- ??????????? `hard` response mode?
- ?????? `strict_success_rate`?`minimal_path_success_rate`?`distractor_action_count`?`evidence_precision`?`evidence_grounding_success`?`contradiction_linking_success`?

## ??

```bash
python scripts/aggregate_results.py --out-dir results/v3_seeded_model_a logs/<run1>.eval logs/<run2>.eval
python scripts/write_run_manifest.py --out-dir results/v3_seeded_model_a --run-name v3_seeded_model_a --response-mode benchmark
```
