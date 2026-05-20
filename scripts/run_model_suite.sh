#!/usr/bin/env bash
set -euo pipefail

RESULT_DIR="${RESULT_DIR:-results/pilot_latest}"
MODELS=("${@:-deepseek-v4-pro deepseek-v4-flash}")

mkdir -p "${RESULT_DIR}"
: > "${RESULT_DIR}/run_logs.tsv"

if (( $# == 0 )); then
  MODELS=("deepseek-v4-pro" "deepseek-v4-flash")
fi

for model in "${MODELS[@]}"; do
  RESULT_DIR="${RESULT_DIR}" bash scripts/run_repeated.sh "${model}" 1
done

mapfile -t logs < <(cut -f3 "${RESULT_DIR}/run_logs.tsv" | awk 'NF')
if (( ${#logs[@]} == 0 )); then
  echo "No logs were recorded in ${RESULT_DIR}/run_logs.tsv" >&2
  exit 1
fi

python scripts/aggregate_results.py --out-dir "${RESULT_DIR}" "${logs[@]}"
