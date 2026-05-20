#!/usr/bin/env bash
set -euo pipefail

export XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/honeyagentbench_inspect_data}"

inspect eval honeyagentbench/tasks.py@honeyagent_pilot \
  --solver inspect_cyber/verify_solutions \
  -T root_dir=evals
