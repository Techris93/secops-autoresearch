#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/data/openclaw/logs"
TIMESTAMP="$(date +"%Y%m%d-%H%M%S")"
LOG_FILE="$LOG_DIR/live-run-$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

cd "$ROOT_DIR"
source "$ROOT_DIR/.venv/bin/activate"

echo "[info] $(date -u +"%Y-%m-%dT%H:%M:%SZ") starting run_openclaw_live.py" | tee -a "$LOG_FILE"
python "$ROOT_DIR/run_openclaw_live.py" "$@" 2>&1 | tee -a "$LOG_FILE"
echo "[info] $(date -u +"%Y-%m-%dT%H:%M:%SZ") completed" | tee -a "$LOG_FILE"

echo "[info] latest findings"
python "$ROOT_DIR/soc_store.py" list | head -20

echo "[info] log file: $LOG_FILE"
