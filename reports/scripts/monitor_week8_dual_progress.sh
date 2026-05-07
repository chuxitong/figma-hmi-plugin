#!/usr/bin/env bash
# Append human-readable snippets to WEEK8_DUAL_PROGRESS_LOG until both runs finish or pipeline dies.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
B="${ROOT}/reports/deliverables_week8_prompt_baseline/metrics_full.json"
E="${ROOT}/reports/deliverables_week8_prompt_extended/metrics_full.json"
LOG="${WEEK8_DUAL_PROGRESS_LOG:-/tmp/week8_dual_progress.log}"
MAIN="${MAIN_LOGBUNDLE:-/tmp/hmi_week8_two_profiles.log}"
INTERVAL="${POLL_INTERVAL_SEC:-180}"

touch "$LOG"
echo "===== monitor start $(date -Is) interval=${INTERVAL}s =====" >>"$LOG"

while true; do
  ts="$(date -Is)"
  hv="$(curl -sS --max-time 3 http://127.0.0.1:8000/health 2>/dev/null | head -c 260 || echo '{}')"
  gpu="$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null | head -1 || echo 'no_smi')"
  comp="$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv 2>/dev/null | tail -n +2 | head -5 | tr '\n' ' ' || true)"
  bm="no"; em="no"
  [[ -f "$B" ]] && bm="yes"
  [[ -f "$E" ]] && em="yes"
  alive=0
  pgrep -f run_week8_two_profiles.sh >/dev/null 2>&1 && alive=1
  pgrep -f 'hmi_week78_eval\.py.*--week 8' >/dev/null 2>&1 && alive=1
  {
    echo "[$ts] baseline_metrics_full=$bm extended_metrics_full=$em alive_pipeline=$alive"
    echo "health: $hv"
    echo "gpu: $gpu compute_apps: ${comp:-none}"
    if [[ "$alive" -eq 1 ]]; then
      echo "--- processes (sample) ---"
      pgrep -af run_week8_two_profiles.sh 2>/dev/null | head -3 || true
      pgrep -af 'hmi_week78_eval\.py.*--week 8' 2>/dev/null | head -3 || true
    else
      echo "(no parent/child week8 processes this tick)"
    fi
    echo "--- tail $MAIN ---"
    tail -4 "$MAIN" 2>/dev/null | sed 's/^/  /'
  } >>"$LOG"

  if [[ "$bm" == yes && "$em" == yes ]]; then
    echo "[$ts] STATUS=COMPLETE_BOTH_METRICS" >>"$LOG"
    touch /tmp/week8_DUAL_DONE.flag
    grep -aE 'Week 8 artefacts|^Done →' "$MAIN" 2>/dev/null >>"$LOG" || true
    exit 0
  fi

  if [[ "$alive" -eq 0 ]]; then
    echo "[$ts] STATUS=EXITED_WITHOUT_BOTH_ARTEFACTS" >>"$LOG"
    tail -60 "$MAIN" >>"$LOG" 2>/dev/null || true
    exit 1
  fi

  sleep "$INTERVAL"
done
