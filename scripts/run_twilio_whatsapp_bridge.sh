#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/.venv/bin/activate"

: "${SECOPS_TWILIO_AUTH_TOKEN:=}"
: "${SECOPS_PUBLIC_WEBHOOK_URL:=}"
: "${SECOPS_ALLOW_UNSIGNED:=0}"

python "$ROOT_DIR/twilio_whatsapp_webhook.py" --host 127.0.0.1 --port 8091
