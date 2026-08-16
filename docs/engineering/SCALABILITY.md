# Scalability Path

## Stage 0 — local

One Compose stack. Optimize for developer experience.

## Stage 1 — beta

- stateless API replicas
- managed PostgreSQL
- Redis with persistence/HA where needed
- object storage for media
- background worker replicas
- CDN for static assets

## Stage 2 — growth

Split hot paths by workload:

```text
API
├── Tutor API
├── Speech API
├── Learning API
└── Companion API

Workers
├── STT
├── TTS
├── avatar inference
├── analytics
└── notifications
```

Scale GPU inference independently from the API tier.

## Stage 3 — global

- multi-region edge routing
- regional model inference
- tenant-aware rate limits
- regional data residency where required
- asynchronous event pipeline
- dedicated model gateway with provider health scoring

Do not prematurely split services. Measure latency, CPU, memory, queue depth and failure rates first.
