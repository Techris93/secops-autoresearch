#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/.venv/bin/activate"

echo "[1/5] Generate deterministic synthetic attacks + benign background"
python prepare.py

echo "[2/5] Baseline benchmark (with per-rule/missed breakdown)"
python evaluate.py --verbose

echo "[3/5] Optional OpenClaw attack-mix generation"
if [[ -f "$ROOT_DIR/generate_openclaw_attack_mix.py" ]]; then
  python generate_openclaw_attack_mix.py --stats || true
fi

echo "[4/5] Auto-research threshold tuning (quick sweep)"
python tune.py --quick --output data/tune_results_quick.json

echo "[5/5] Re-run benchmark after tuning exploration"
python evaluate.py

echo

echo "Done."
echo "- Quick tuning report: data/tune_results_quick.json"
echo "- Latest benchmark artifacts: data/best.json, data/per_rule_metrics.json"
echo "- Next: apply recommended thresholds in detect.py, then run python evaluate.py --commit"
