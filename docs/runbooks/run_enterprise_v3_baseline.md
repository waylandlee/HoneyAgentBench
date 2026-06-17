# ?? Enterprise v3 Static Baseline

? runbook ??????? enterprise v3 ?????

## ??

```text
eval: multinode-enterprise-v3-static-baseline
seed: v3-static-baseline
response_mode: debug
```

????????? v3 ???????? seeded ???? hard ???

## Solution verify

```bash
inspect eval honeyagentbench/tasks.py@honeyagent_pilot   --solver inspect_cyber/verify_solutions   -T root_dir=evals   -T eval_names=multinode-enterprise-v3-static-baseline
```

## ????????

```bash
bash scripts/run_deepseek.sh deepseek-v4-pro multinode-enterprise-v3-static-baseline baseline-react
```

## ??? manifest

```bash
python scripts/aggregate_results.py --out-dir results/v3_static_baseline logs/<run>.eval
python scripts/write_run_manifest.py   --out-dir results/v3_static_baseline   --run-name v3_static_baseline   --model deepseek-v4-pro   --eval-name multinode-enterprise-v3-static-baseline   --scenario-seed v3-static-baseline   --response-mode debug   --score-log logs/<run>.eval   --env-key DEEPSEEK_API_KEY
```

??? API key ?????????????
