#!/bin/sh
set -e

echo "[entrypoint] Running database migrations..."
alembic upgrade head

echo "[entrypoint] Starting gunicorn..."
exec gunicorn -w 4 \
  --timeout 1200 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --log-level info \
  -b 0.0.0.0:5000 \
  app.app:app
