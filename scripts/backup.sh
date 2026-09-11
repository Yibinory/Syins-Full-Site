#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "Missing .env. Run scripts/install.sh first." >&2
  exit 1
fi

mkdir -p data/backups
STAMP=$(date +%Y%m%d-%H%M%S)
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > "data/backups/database-${STAMP}.sql"
docker compose exec -T backend sh -c 'tar czf - -C /app/data/uploads .' > "data/backups/media-${STAMP}.tar.gz"
echo "Backup written to data/backups/database-${STAMP}.sql and data/backups/media-${STAMP}.tar.gz"
