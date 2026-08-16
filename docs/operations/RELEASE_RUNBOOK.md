# Release & Rollback Runbook

## Before release

- CI green
- dependency/security scans green
- AI evaluation suite green
- database migration reviewed
- backup verified
- release notes prepared
- rollback artifact available

## Deploy

1. deploy backend/API;
2. run migrations with compatibility checks;
3. deploy workers;
4. run health and smoke tests;
5. release mobile/web artifacts progressively;
6. monitor golden signals.

## Rollback

Rollback immediately when:

- error rate breaches the agreed threshold;
- authentication is broken;
- data integrity is at risk;
- critical privacy/security issue is detected;
- core tutor flow is unavailable.

Prefer backward-compatible database migrations so application rollback does not require destructive schema changes.
