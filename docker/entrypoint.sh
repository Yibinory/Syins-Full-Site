#!/bin/sh
set -eu

mkdir -p /app/data/database /app/data/uploads /app/data/backups /app/data/static

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ "${SEED_DEMO:-false}" = "true" ]; then
  echo "Ensuring the initial Research OS workspace exists..."
  python manage.py seed_demo
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
