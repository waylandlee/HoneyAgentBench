#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-deepseek-v4-pro}"
RUNS="${2:-1}"
RESULT_DIR="${RESULT_DIR:-results/pilot_latest}"
MANIFEST="${RESULT_DIR}/run_logs.tsv"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/honeyagentbench_inspect_data}"

if ! [[ "${RUNS}" =~ ^[0-9]+$ ]]; then
  echo "runs must be an integer between 1 and 2" >&2
  exit 2
fi

if (( RUNS < 1 || RUNS > 2 )); then
  echo "runs must be between 1 and 2; refusing to exceed the per-model limit" >&2
  exit 2
fi

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
mkdir -p "${RESULT_DIR}" logs

for run_index in $(seq 1 "${RUNS}"); do
  echo "Running ${MODEL}, run ${run_index}/${RUNS}"
  inspect eval honeyagentbench/tasks.py@honeyagent_pilot \
    --model "openai/${MODEL}" \
    --model-base-url "${BASE_URL}" \
    -T root_dir=evals

  latest_log="$(
    find logs -maxdepth 1 -type f -name '*.eval' -printf '%T@ %p\n' \
      | sort -nr \
      | head -n 1 \
      | cut -d' ' -f2-
  )"
  if [[ -z "${latest_log}" ]]; then
    echo "No Inspect .eval log was found after running ${MODEL}" >&2
    exit 1
  fi
  printf '%s\t%s\t%s\n' "${MODEL}" "${run_index}" "${latest_log}" >> "${MANIFEST}"
done
