#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

export PYTHONUNBUFFERED=1
exec uvicorn app.main:create_app --factory --host "${MYTUBE_HOST:-0.0.0.0}" --port "${MYTUBE_PORT:-8000}" --reload
