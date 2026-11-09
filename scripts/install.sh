#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
npm --cache "${TMPDIR:-/tmp}/morny-npm" --prefix frontend ci
npm --prefix frontend run build
(cd backend && ../.venv/bin/python -m alembic upgrade head)
