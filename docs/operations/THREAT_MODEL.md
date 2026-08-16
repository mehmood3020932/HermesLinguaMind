# Threat Model

## Assets

- account credentials and sessions
- user profile and learning history
- voice/audio data
- model/provider credentials
- avatar media
- application infrastructure

## Threats

| Threat | Mitigation |
|---|---|
| Credential theft | secure cookies/tokens, rotation, rate limits |
| Prompt injection | trust boundaries, tool allowlists, output validation |
| Data leakage | minimization, redaction, access controls |
| API abuse | quotas, rate limits, anomaly detection |
| Avatar impersonation | fictional/default characters, consent rules, provenance/licensing |
| Supply-chain compromise | pinned dependencies, lockfiles, CI scanning |
| Container escape | least privilege, minimal images, patching |
| Secret exposure | `.env` ignored, secret manager in production |

## Security baseline

No service should expose PostgreSQL, Redis, Elasticsearch or internal admin ports directly to the public internet.
