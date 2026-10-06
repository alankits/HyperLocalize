#!/usr/bin/env bash
# Development-only PostgreSQL without sudo or Docker.
# Downloads the official-build binaries packaged by the zonky embedded-postgres project
# (Maven Central), verifies the published SHA-1, and runs a cluster on a local Unix socket.
# The supported way to run HyperLocalize is Docker Compose (ADR 0012); this is a stopgap.
set -euo pipefail
VERSION=17.11.0
BASE=https://repo1.maven.org/maven2/io/zonky/test/postgres/embedded-postgres-binaries-linux-amd64/$VERSION
DIR=${HL_DEV_PG_DIR:-$HOME/.local/hl-dev}
PORT=${HL_DB_PORT:-5433}
mkdir -p "$DIR/run"
cd "$DIR"
if [ ! -x pg/bin/postgres ]; then
  curl -fsS -o pg.jar "$BASE/embedded-postgres-binaries-linux-amd64-$VERSION.jar"
  expected=$(curl -fsS "$BASE/embedded-postgres-binaries-linux-amd64-$VERSION.jar.sha1")
  echo "$expected  pg.jar" | sha1sum -c -
  python3 -c "import zipfile; zipfile.ZipFile('pg.jar').extract('postgres-linux-x86_64.txz', '.')"
  mkdir -p pg && tar -xJf postgres-linux-x86_64.txz -C pg
fi
if [ ! -d data ]; then
  pg/bin/initdb -D data -U hl --auth=trust -E UTF8 --locale=C.UTF-8 >/dev/null
fi
case "${1:-start}" in
  start)
    pg/bin/pg_ctl -D data status >/dev/null 2>&1 || \
      pg/bin/pg_ctl -D data -o "-p $PORT -k $DIR/run -c listen_addresses=''" -l pg.log start
    ;;
  stop) pg/bin/pg_ctl -D data stop ;;
  status) pg/bin/pg_ctl -D data status ;;
esac
