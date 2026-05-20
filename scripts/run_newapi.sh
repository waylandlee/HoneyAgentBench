#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-gpt-5.5}"
BASE_URL="${NEWAPI_BASE_URL:-https://api.ikuncode.cc/v1}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/honeyagentbench_inspect_data}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

BASE_URL="${NEWAPI_BASE_URL:-${BASE_URL}}"

if [[ -z "${NEWAPI_API_KEY:-}" ]]; then
  echo "NEWAPI_API_KEY is not set. Add it to .env or export it in the shell." >&2
  exit 2
fi

export OPENAI_API_KEY="${NEWAPI_API_KEY}"

inspect eval honeyagentbench/tasks.py@honeyagent_pilot \
  --model "openai/${MODEL}" \
  --model-base-url "${BASE_URL}" \
  -T root_dir=evals
