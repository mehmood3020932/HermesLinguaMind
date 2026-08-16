#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${HERMES_BASE_URL:-http://localhost}"

echo "== Hermes smoke test: $BASE_URL =="
health="$(curl -fsS "$BASE_URL/health")"
echo "$health" | grep -q 'healthy' || { echo "Gateway is not healthy" >&2; exit 1; }
services="$(curl -fsS "$BASE_URL/v1/services")"
echo "$services" | grep -q 'services' || { echo "Service registry unavailable" >&2; exit 1; }

echo "Health: PASS"
echo "Service registry: PASS"
echo "Website: $(curl -fsS -o /dev/null -w '%{http_code}' "$BASE_URL/")"
echo "Smoke test complete."
