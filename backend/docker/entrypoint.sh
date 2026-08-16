#!/bin/sh
# =============================================================================
# Hermes LinguaMind — entrypoint for the single consolidated backend
# container. Waits for postgres/redis (external infra containers) to accept
# connections before handing off to supervisord, so the 22 services don't
# all crash-loop through their first few restarts on a cold `docker compose up`.
# =============================================================================
set -e

wait_for() {
  host="$1"
  port="$2"
  name="$3"
  tries=0
  max_tries=60
  echo "[entrypoint] waiting for ${name} at ${host}:${port} ..."
  while ! python3 -c "import socket,sys; s=socket.socket(); s.settimeout(1); sys.exit(0 if s.connect_ex(('${host}', ${port}))==0 else 1)" 2>/dev/null; do
    tries=$((tries + 1))
    if [ "$tries" -ge "$max_tries" ]; then
      echo "[entrypoint] WARNING: ${name} still not reachable after ${max_tries}s — starting anyway (supervisord will auto-restart services until it is up)."
      return 0
    fi
    sleep 1
  done
  echo "[entrypoint] ${name} is up."
}

if [ -n "${DATABASE_HOST:-}" ]; then
  wait_for "${DATABASE_HOST}" "${DATABASE_PORT:-5432}" "postgres"
fi

if [ -n "${REDIS_HOST:-}" ]; then
  wait_for "${REDIS_HOST}" "${REDIS_PORT:-6379}" "redis"
fi

# Seed default avatar characters (hermes-default, maria-spanish-tutor) so
# POST /svc/avatar/v1/sessions works out of the box on a fresh database —
# this was previously a documented-but-never-invoked script (see
# scripts/seed_avatar_characters.py), meaning avatar session creation
# 404'd on any clean deploy. Idempotent (skips existing slugs) and
# non-fatal: a seed failure logs and falls through to starting the stack
# rather than blocking it, matching this entrypoint's existing pattern of
# never letting one optional step take down the whole container.
echo "[entrypoint] seeding default avatar characters..."
python3 /app/scripts/seed_avatar_characters.py || echo "[entrypoint] WARNING: avatar character seeding failed — avatar_service will 404 on unseeded character slugs until this is re-run."

echo "[entrypoint] starting supervisord — 22 services + orchestrator + adapter + celery worker."
exec supervisord -c /etc/supervisor/conf.d/hermes.conf
