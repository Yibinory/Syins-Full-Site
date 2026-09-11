#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "Missing .env. Run scripts/install.sh first." >&2
  exit 1
fi

docker compose build --pull
docker compose up -d
docker compose ps
echo "Update complete. Database migrations ran in the backend startup process."
