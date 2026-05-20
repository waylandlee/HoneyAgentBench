#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-deepseek-v4-pro}"
EVAL_NAMES="${2:-}"
VARIANT_NAMES="${3:-}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/honeyagentbench_inspect_data}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is not set. Add it to .env or export it in the shell." >&2
  exit 2
fi

export OPENAI_API_KEY="${DEEPSEEK_API_KEY}"

ARGS=(
  inspect eval honeyagentbench/tasks.py@honeyagent_pilot
  --model "openai/${MODEL}"
  --model-base-url "${BASE_URL}"
  -T root_dir=evals
)

if [[ -n "${EVAL_NAMES}" ]]; then
  ARGS+=(-T "eval_names=${EVAL_NAMES}")
fi

if [[ -n "${VARIANT_NAMES}" ]]; then
  ARGS+=(-T "variant_names=${VARIANT_NAMES}")
fi

"${ARGS[@]}"
