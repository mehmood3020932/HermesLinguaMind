# Complete Architecture

![System architecture](../assets/architecture-system.svg)

## Design goals

1. **Local-first** — use open models where practical and make external providers explicit.
2. **Provider-neutral** — LLM, STT, TTS and avatar engines are adapters, not domain dependencies.
3. **Domain-first** — learning, progress, memory and safety remain independent from presentation.
4. **Observable** — every production request has a correlation ID, structured logs, metrics and trace context.
5. **Safe-by-default** — secrets, PII, model licenses and moderation are treated as first-class concerns.
6. **Scale without rewrite** — the local all-in-one Compose stack can evolve toward independently scaled services.

## Runtime boundaries

```text
Flutter / Web
   │ HTTPS + WebSocket/WebRTC
   ▼
Edge / Nginx
   │
   ▼
API Gateway ─────────────── Auth / Rate limits / Request IDs
   │
   ▼
Hermes Orchestrator
   ├── Intent + policy
   ├── Tutor planner
   ├── LLM adapter
   ├── Memory adapter
   ├── Learning engine
   ├── Voice pipeline
   └── Companion adapter
        ├── CPU renderer
        └── OpenTalking / WebRTC

Persistence
├── PostgreSQL: transactional state
├── Redis: ephemeral state, queues, rate limits
└── Elasticsearch: search/retrieval/analytics where enabled

Observability
├── structured logs
├── metrics
├── traces
└── audit events
```

## Deployment modes

### Development

One Compose project with local models and infrastructure. Optimize for reproducibility and low cognitive load.

### Staging

Use separate secrets, managed backups, HTTPS, observability, migrations, smoke tests and a real domain. External avatar/LLM credentials are explicitly configured.

### Production

Stateless API replicas behind a load balancer, separately scaled workers, managed PostgreSQL/Redis/search where appropriate, object storage for media, centralized telemetry, automated backups and a rollback strategy.

## Failure boundaries

- LLM unavailable → deterministic fallback response + retry policy.
- TTS unavailable → text response and optional cached voice.
- Avatar unavailable → CPU/static companion mode; learning continues.
- Redis unavailable → degrade ephemeral features; never lose durable progress.
- Search unavailable → primary database fallback for critical paths.
- External provider timeout → circuit breaker and provider health state.

The learning domain must never depend on the avatar being available.
