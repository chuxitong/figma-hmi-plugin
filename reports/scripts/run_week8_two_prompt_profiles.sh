#!/usr/bin/env bash
# Run Week 8 twice: UI2CODEN_PROMPT_PROFILE=baseline then extended.
# Restart local-service uvicorn between runs so prompt template matches env.
#
# Fixed X-Experiment-Trace-Dir (baseline → symlink to legacy stamp dir; extended → real dir)
# keeps server-side prompts under ONE root per profile across resumes.
#
# Usage (from repo root):
#   API_BASE=http://127.0.0.1:8000 bash reports/scripts/run_week8_two_prompt_profiles.sh
#
# Interrupted run — same paths, append resume:
#   WEEK8_RESUME=1 API_BASE=... bash reports/scripts/run_week8_two_prompt_profiles.sh
#
# Python args are passed via arrays (no trailing-\ line continuations) so CRLF from
# Windows editors cannot break continuation and turn "--force-refine-rounds" into a bogus command.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export API_BASE="${API_BASE:-http://127.0.0.1:8000}"
export USE_REAL_MODEL="${USE_REAL_MODEL:-1}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
PY="${ROOT}/local-service/.venv/bin/python"
BASE_OUT="${ROOT}/reports/deliverables_week8_prompt_baseline"
EXT_OUT="${ROOT}/reports/deliverables_week8_prompt_extended"
TRACE_BASE="${ROOT}/reports/deliverables_week8_prompt_baseline/reproducibility_logs/WEEK8_FIXED_SERVER_TRACE_ROOT"
TRACE_EXT="${ROOT}/reports/deliverables_week8_prompt_extended/reproducibility_logs/WEEK8_FIXED_SERVER_TRACE_ROOT"

_run_week8_for_profile() {
  local prof="$1"
  local deliver="$2"
  local trace="$3"
  local -a args=(
    "${ROOT}/reports/scripts/hmi_week78_eval.py"
    --week 8
    --force-refine-rounds 2
    --max-refines 2
    --week8-deliver-dir "${deliver}"
    --trace-dir "${trace}"
  )
  if [[ "${WEEK8_RESUME:-0}" == "1" ]]; then
    args+=(--week8-resume)
  fi
  ( cd "${ROOT}/local-service" && export UI2CODEN_PROMPT_PROFILE="${prof}" && bash start_cloud_service.sh )
  "${PY}" "${args[@]}"
}

_run_week8_for_profile baseline "${BASE_OUT}" "${TRACE_BASE}"
_run_week8_for_profile extended "${EXT_OUT}" "${TRACE_EXT}"

echo "Done → ${BASE_OUT} and ${EXT_OUT}"
