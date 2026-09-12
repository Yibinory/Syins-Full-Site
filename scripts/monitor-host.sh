#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
METRICS_DIR="$ROOT_DIR/data/host-metrics"
PID_FILE="$METRICS_DIR/sampler.pid"
SAMPLER="$ROOT_DIR/backend/apps/servers/host_metrics.py"
mkdir -p "$METRICS_DIR"
active() {
  [ -f "$PID_FILE" ] || return 1
  SAMPLER_PID=$(cat "$PID_FILE")
  case "$SAMPLER_PID" in ''|*[!0-9]*) return 1;; esac
  kill -0 "$SAMPLER_PID" 2>/dev/null || return 1
  ps -p "$SAMPLER_PID" -o command= | grep -F -- "$SAMPLER" >/dev/null
}
case "${1:-start}" in
  start)
    if active; then echo "Host sampler already running."; exit 0; fi
    PYTHON_BIN=${PYTHON_BIN:-python3}
    "$PYTHON_BIN" "$SAMPLER" --output "$METRICS_DIR/snapshot.json" --once
    nohup "$PYTHON_BIN" "$SAMPLER" --output "$METRICS_DIR/snapshot.json" --interval 30 > "$METRICS_DIR/sampler.log" 2>&1 < /dev/null &
    echo "$!" > "$PID_FILE"
    echo "Host sampler started."
    ;;
  stop)
    if active; then kill "$SAMPLER_PID"; fi
    rm -f "$PID_FILE"
    echo "Host sampler stopped."
    ;;
  status)
    if active; then echo "Host sampler running."; else echo "Host sampler stopped."; exit 1; fi
    ;;
  *) echo "Usage: $0 start|stop|status" >&2; exit 1;;
esac
