#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0
required=(README.md LICENSE CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md ROADMAP.md Makefile backend/.env.example backend/docker-compose.yml mobile_app/pubspec.yaml)
for f in "${required[@]}"; do
  if [[ -f "$f" ]]; then echo "[OK] $f"; else echo "[FAIL] missing $f"; fail=1; fi
done

if [[ -f backend/.env ]]; then
  echo "[FAIL] backend/.env exists — remove secrets before committing"
  fail=1
else
  echo "[OK] no backend/.env committed"
fi

if find . -type f \( -name '*.pem' -o -name '*.key' \) -not -path './.git/*' | grep -q .; then
  echo "[FAIL] private key material found in repository"
  fail=1
else
  echo "[OK] no obvious private-key files"
fi

if command -v docker >/dev/null 2>&1; then
  if docker compose -f backend/docker-compose.yml config >/dev/null 2>&1; then
    echo "[OK] Docker Compose config parses"
  else
    echo "[WARN] Docker Compose config could not be validated by the local Docker installation"
  fi
else
  echo "[INFO] Docker not installed; skipping compose validation"
fi

if command -v python >/dev/null 2>&1; then
  if python -m compileall -q backend; then echo "[OK] Python bytecode compilation"; else echo "[FAIL] Python compilation"; fail=1; fi
else
  echo "[INFO] Python not installed; skipping Python compilation"
fi

if [[ "$fail" -ne 0 ]]; then exit 1; fi
echo "Hermes repository doctor: PASS"
