#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f backend/.env ]]; then cp backend/.env.example backend/.env; fi

echo "Hermes environment initialized."
echo "Next: review backend/.env, then run 'make doctor' and 'make up'."
