#!/bin/sh
set -eu

# ADR 0025: migrate before serving so the app never runs against a stale schema.
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --log-level "${LOG_LEVEL}"
