#!/usr/bin/env bash
# Development helper without Docker: dev Postgres, migrations, one worker, and the web server.
# Docker Compose (docker compose up) is the supported way once Docker is installed (ADR 0012).
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/dev_postgres.sh start
PY=.venv/bin/python
$PY manage.py migrate --noinput
$PY manage.py createcachetable
$PY manage.py run_worker --lane all &
WORKER=$!
trap 'kill $WORKER 2>/dev/null' EXIT
$PY manage.py runserver 127.0.0.1:8000
