#!/usr/bin/env bash
# Poll until Week 8 dual-profile deliverables are complete, then exit 0 (for
# Cursor background task --> user notification). Exit 1 if the pipeline dies early.
#
# On success, validates both metrics_full.json (VKR-facing): model_backend ui2coden,
# 24 grid rows, context_source_bulk=synthetic_script (honest labelling for variables/CSS).
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
B="${ROOT}/reports/deliverables_week8_prompt_baseline/metrics_full.json"
E="${ROOT}/reports/deliverables_week8_prompt_extended/metrics_full.json"
MAIN="${MAIN_LOGBUNDLE:-/tmp/hmi_week8_two_profiles.log}"
INTERVAL="${WEEK8_NOTIFY_POLL_SEC:-90}"
# Tolerate short gaps between hmi_week78_eval and uvicorn restarts (or slow health).
DEAD_ROUNDS="${WEEK8_NOTIFY_DEAD_ROUNDS:-6}"
dead_streak=0

_validate_metrics_full_pair() {
  python3 - "$B" "$E" <<'PY'
import json, sys
from pathlib import Path

def load(path: str, label: str) -> dict:
    p = Path(path)
    if not p.is_file():
        print(f"VALIDATION_FAIL: missing {label} {path}", file=sys.stderr)
        sys.exit(2)
    return json.loads(p.read_text(encoding="utf-8"))

def check(d: dict, label: str, expect_rows: int | None) -> int:
    if d.get("model_backend") != "ui2coden":
        print(
            f"VALIDATION_FAIL: {label} model_backend={d.get('model_backend')!r} "
            "(VKR must not mix rule_based with UI2Code^N labelled runs).",
            file=sys.stderr,
        )
        sys.exit(2)
    rows = d.get("per_row_csv") or []
    n = len(rows)
    if expect_rows is not None and n != expect_rows:
        print(
            f"VALIDATION_FAIL: {label} per_row_csv len={n} expected {expect_rows}",
            file=sys.stderr,
        )
        sys.exit(2)
    ctx = d.get("context_source_bulk")
    if ctx != "synthetic_script":
        print(
            f"VALIDATION_WARN: {label} context_source_bulk={ctx!r} "
            "(expected synthetic_script for scripted variables/CSS slice).",
            file=sys.stderr,
        )
    return n

base_path, ext_path = sys.argv[1], sys.argv[2]
db = load(base_path, "baseline")
de = load(ext_path, "extended")
nb = check(db, "baseline", None)
ne = check(de, "extended", nb)
if nb != ne:
    print(f"VALIDATION_FAIL: row count mismatch baseline={nb} extended={ne}", file=sys.stderr)
    sys.exit(2)
print(
    f"VALIDATION_OK: both profiles ui2coden, {nb} rows each; "
    "baseline+extended metrics_full aligned for VKR."
)
PY
}

echo "[week8-notify] watching baseline+extended metrics every ${INTERVAL}s ($(date -Is)) dead_rounds=${DEAD_ROUNDS}"

while true; do
  if [[ -f "$B" && -f "$E" ]]; then
    echo ""
    echo "=== WEEK8 DUAL RUN COMPLETE ==="
    echo "OK: baseline 与 extended 的 metrics_full.json 均已生成。"
    echo "baseline:  $B"
    echo "extended:  $E"
    if ! _validate_metrics_full_pair; then
      echo "metrics 文件存在但校验未通过，退出码 2。"
      exit 2
    fi
    if grep -q 'Done →' "$MAIN" 2>/dev/null; then
      echo "编排日志已出现 Done 行。"
    else
      echo "(编排日志尚未检索到 Done 行；以 metrics 文件与校验为准。)"
    fi
    if [[ -f /tmp/week8_DUAL_DONE.flag ]]; then
      echo "monitor 标记存在: /tmp/week8_DUAL_DONE.flag"
    fi
    exit 0
  fi

  alive=0
  pgrep -f run_week8_two_prompt_profiles.sh >/dev/null 2>&1 && alive=1
  pgrep -f 'hmi_week78_eval\.py.*--week 8' >/dev/null 2>&1 && alive=1
  pgrep -f 'uvicorn app:app' >/dev/null 2>&1 && alive=1

  if [[ "$alive" -eq 0 ]]; then
    dead_streak=$((dead_streak + 1))
    if [[ "$dead_streak" -ge "$DEAD_ROUNDS" ]]; then
      echo ""
      echo "=== WEEK8 DUAL RUN STOPPED EARLY (metrics incomplete) ==="
      echo "baseline metrics_full.json:  $([[ -f $B ]] && echo yes || echo no)"
      echo "extended metrics_full.json: $([[ -f $E ]] && echo yes || echo no)"
      echo "--- last /health (best effort) ---"
      curl -sS --max-time 8 http://127.0.0.1:8000/health 2>/dev/null || echo "(no API)"
      echo "--- tail $MAIN ---"
      tail -100 "$MAIN" 2>/dev/null || true
      exit 1
    fi
  else
    dead_streak=0
  fi

  sleep "$INTERVAL"
done
