# ADR-0003: Compose development stack

## Status
Accepted

## Decision
Use Docker Compose as the primary local orchestration path while keeping the architecture ready for independently scaled services.

## Consequences
Developers get a reproducible environment with fewer moving parts; production can migrate to managed services and orchestration when justified by scale.
