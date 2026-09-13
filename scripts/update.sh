#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "Missing .env. Run scripts/install.sh first." >&2
  exit 1
fi

mkdir -p data/deployment
python3 scripts/deployment_manager.py stop

if grep -q 'docker-compose.images.yml' .env; then
  docker compose pull
else
  docker compose build --pull
fi
docker compose up -d
docker compose ps
python3 scripts/deployment_manager.py start
echo "Update complete. Database migrations ran in the backend startup process."
