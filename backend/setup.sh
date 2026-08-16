#!/usr/bin/env bash
# ============================================================
# Hermes LinguaMind — One-click setup & startup
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

info "Checking prerequisites..."
need_cmd docker
need_cmd curl

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  fail "Docker Compose v2 (docker compose) is required"
fi

if [ ! -f .env ]; then
  cp .env.example .env
  warn "Created .env from .env.example — change SECRET_KEY / DATABASE_PASSWORD for production"
else
  info ".env present"
fi

info "Validating compose file..."
"${COMPOSE[@]}" --env-file .env config >/dev/null

info "Building and starting the unified stack..."
"${COMPOSE[@]}" --env-file .env up -d --build

info "Waiting for unified adapter health..."
READY=0
for i in $(seq 1 36); do
  if curl -fsS http://localhost:8080/health >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 5
done

if [ "$READY" -ne 1 ]; then
  warn "Adapter not healthy after ~3 minutes. Recent logs:"
  "${COMPOSE[@]}" --env-file .env logs --tail=80 hermes_backend || true
  fail "Startup incomplete — run: make logs"
fi

echo ""
info "Hermes LinguaMind is ready"
echo "  Public entry : http://localhost/"
echo "  API docs     : http://localhost:8080/docs"
echo "  Health       : http://localhost/health"
echo "  Deep health  : http://localhost:8080/health?deep=true"
echo "  Registry     : http://localhost:8080/v1/services"
echo ""
echo "Useful commands:"
echo "  make health   # status check"
echo "  make logs     # follow logs"
echo "  make down     # stop stack"
