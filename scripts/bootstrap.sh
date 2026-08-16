#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f backend/.env ] || cp backend/.env.example backend/.env
if command -v docker >/dev/null 2>&1; then
  docker compose -f backend/docker-compose.yml config >/dev/null
  echo "Docker Compose configuration: OK"
else
  echo "Docker is not installed. Install Docker Engine + Compose v2, then rerun this script." >&2
  exit 1
fi
