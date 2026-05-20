#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-openai/gpt-4o-mini}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/honeyagentbench_inspect_data}"

inspect eval honeyagentbench/tasks.py@honeyagent_pilot \
  --model "$MODEL" \
  -T root_dir=evals
