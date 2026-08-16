#!/usr/bin/env python3
"""
Hermes LinguaMind — demo account seeder.

Registers the demo/reviewer account through the REAL /v1/auth/register
endpoint (so it gets a properly hashed password and passes the same
validation any real signup would) instead of writing directly to the
database. As of this version, api_gateway persists users in Postgres via
UserORM (see shared/models/common.py, shared/database.py) — going through
the real endpoint is still the right call here, it's just no longer a
workaround for a missing table.

Usage (after `docker compose up` / `make up`):
    python3 scripts/seed_demo_user.py
    python3 scripts/seed_demo_user.py --base-url http://localhost:8080

Safe to re-run: a "USER_EXISTS" response is treated as success.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEMO_ACCOUNT = {
    "email": "demo@hermeslingua.app",
    "username": "demo_user",
    "password": "HermesDemo#2026",
    "display_name": "Demo Reviewer",
    "native_language": "en",
    "learning_language": "es",
}


def register(base_url: str) -> int:
    # The unified adapter mounts api_gateway under /svc/api-gateway/... and
    # forwards the remaining path upstream — see src/adapters/registry.py.
    url = f"{base_url.rstrip('/')}/svc/api-gateway/v1/auth/register"
    payload = json.dumps(DEMO_ACCOUNT).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"[seed_demo_user] Could not reach {url}: {exc}")
        print("[seed_demo_user] Is the stack up? Try: make up")
        return 1

    if body.get("success"):
        print(f"[seed_demo_user] Demo account ready: {DEMO_ACCOUNT['email']}")
        return 0

    if body.get("error_code") == "USER_EXISTS":
        print("[seed_demo_user] Demo account already exists — nothing to do.")
        return 0

    print(f"[seed_demo_user] Registration failed: {body}")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="http://localhost:8080",
        help="Unified adapter base URL (default: http://localhost:8080)",
    )
    args = parser.parse_args()
    sys.exit(register(args.base_url))
