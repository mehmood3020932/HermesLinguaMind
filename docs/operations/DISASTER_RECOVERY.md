# Disaster Recovery

## Recovery priorities

1. Authentication and account access
2. Learning progress
3. Tutor API
4. Voice services
5. Companion/avatar services
6. Analytics/search

The avatar is intentionally lower priority than durable learning state.

## Backups

Production should maintain encrypted, tested backups of PostgreSQL and required object storage. Redis should be treated as recoverable state unless a deployment explicitly makes it durable.

## Recovery objectives

Set business-specific RPO/RTO before production. A reasonable initial exercise is:

- RPO: <= 15 minutes for core transactional data
- RTO: <= 60 minutes for the core tutor service

These are targets for infrastructure planning, not guarantees of the current repository.

## Recovery drill

At least quarterly, restore a backup into an isolated environment and run the smoke suite.
