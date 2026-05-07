#!/usr/bin/env bash
# Start uvicorn on 0.0.0.0:8000 with real UI2Code^N defaults (runs on CLOUD Linux).
# See: help/docs/DEPLOYMENT_AUTODL.zh.md
# LOCAL browser access: help/本地浏览器访问云端8000-SSH隧道.zh.md

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

export USE_REAL_MODEL="${USE_REAL_MODEL:-1}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export UI2CODEN_QUANT="${UI2CODEN_QUANT:-none}"
export UI2CODEN_DEVICE_MAP="${UI2CODEN_DEVICE_MAP:-single}"
export UI2CODEN_MODEL_ID="${UI2CODEN_MODEL_ID:-/root/autodl-tmp/UI2Code_N}"
# Uncomment to defer GPU load until first HTTP request:
# export UI2CODEN_SKIP_WARMUP=1

_stop_old_uvicorn_wait_gpu() {
  pkill -TERM -f 'uvicorn app:app' 2>/dev/null || true
  local i
  for i in $(seq 1 60); do
    if ! pgrep -f 'uvicorn app:app' >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  pkill -KILL -f 'uvicorn app:app' 2>/dev/null || true
  sleep 1
  if command -v nvidia-smi >/dev/null 2>&1; then
    for i in $(seq 1 120); do
      local cnt
      cnt="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -c . || true)"
      if [[ "${cnt:-0}" -eq 0 ]]; then
        break
      fi
      sleep 2
    done
  fi
  sleep 2
}

_stop_old_uvicorn_wait_gpu

LOG="${LOG_FILE:-/tmp/uvicorn-figma-hmi.log}"
mkdir -p "$(dirname "$LOG")"
nohup .venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000 >>"$LOG" 2>&1 &
echo "Started uvicorn (host 0.0.0.0 port 8000). PID=$!"
echo "Log file: $LOG"
echo ""

for _ in $(seq 1 60); do
  if curl -sS --max-time 2 "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
    echo "Smoke check: GET /health OK on server loopback."
    curl -sS "http://127.0.0.1:8000/health" | head -c 400 || true
    echo ""
    break
  fi
  sleep 2
done
if ! curl -sS --max-time 2 "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
  echo "Smoke check: /health not ready yet (model warm-up may still be running). Tail log:"
  echo "  tail -f $LOG"
fi

echo ""
echo "=== 在你自己的 Windows/Mac 终端执行（本机浏览器访问云上 8000）==="
echo "  ssh -p 10029 -L 8000:127.0.0.1:8000 root@connect.westd.seetacloud.com -N"
echo "登录（不设端口转发）："
echo "  ssh -p 10029 root@connect.westd.seetacloud.com"
echo "然后在**本机**浏览器打开: http://127.0.0.1:8000/docs"
exit 0
