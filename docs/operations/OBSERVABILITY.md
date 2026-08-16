# Observability & SLOs

## Golden signals

Track:

- latency
- traffic
- errors
- saturation

For AI features also track:

- STT latency
- LLM time-to-first-token
- TTS latency
- avatar first-frame latency
- provider failure rate
- fallback rate
- cost per active learner

## Suggested initial SLOs

These are targets to validate, not claims about the current system.

| Service | Target |
|---|---|
| API availability | 99.9% monthly |
| Tutor text response | p95 < 4s under agreed workload |
| STT | p95 < 3s for short utterances |
| TTS | p95 < 3s to first audio |
| Avatar first frame | p95 < 8s for heavy inference; lower for cached/CPU mode |

## Logging rules

Use JSON logs with:

- timestamp
- level
- service
- request_id
- trace_id
- event
- latency_ms
- outcome

Never log secrets or raw sensitive user content by default.
