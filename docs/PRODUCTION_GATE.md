# Production Gate

This checklist prevents the repository from being called production-ready merely because it builds.

## P0 — must pass

- [ ] No secrets in Git history
- [ ] `make doctor` passes
- [ ] `docker compose config` passes
- [ ] Backend image builds from a clean checkout
- [ ] Nginx serves the website
- [ ] `/health` is healthy
- [ ] `/v1/services` returns the expected registry
- [ ] `/v1/chat` produces a real backend response
- [ ] PostgreSQL migrations/init succeed
- [ ] Redis is healthy
- [ ] Ollama model is available or an explicitly configured remote provider is healthy
- [ ] Mobile app builds in release mode
- [ ] Mobile app can reach the gateway on emulator and physical device
- [ ] Error states are visible and recoverable

## P1 — strongly recommended

- [ ] HTTPS + real domain
- [ ] restrictive CORS
- [ ] rate limits tuned
- [ ] backups and restore drill
- [ ] structured logs + metrics
- [ ] crash reporting
- [ ] privacy policy + terms
- [ ] app-store metadata
- [ ] model/voice/avatar licenses reviewed
- [ ] accessibility pass
- [ ] load test of the gateway

## P2 — scale readiness

- [ ] Kubernetes deployment tested
- [ ] external object storage for media
- [ ] managed PostgreSQL/Redis/Elasticsearch where appropriate
- [ ] queue autoscaling
- [ ] GPU worker pool for real-time avatar inference
- [ ] CDN for static web/media assets
- [ ] blue/green or canary release strategy
