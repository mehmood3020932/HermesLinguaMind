# Architecture

## High-level

```text
                    Flutter Mobile
                         │
                 HTTPS / WebRTC
                         │
                         ▼
                  Nginx / Gateway
                         │
                         ▼
                Hermes Orchestrator
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      LLM              Voice            Learning
   Ollama/API        STT → TTS        Curriculum
        │                │                │
        └────────────────┼────────────────┘
                         ▼
             Memory / Personalization
                         │
                         ▼
              Avatar / Viseme / Emotion
                         │
                         ▼
                    Flutter UI

Infrastructure: PostgreSQL + Redis + Elasticsearch
Optional: OpenTalking avatar API/worker/web + GPU inference
```

## Backend philosophy

The repository consolidates application services into a single backend image for local simplicity while keeping infrastructure services separate. The phase directories reflect the original implementation history; the public contract should be treated as the gateway/API layer rather than as a promise that every internal service is independently deployable.

## AI provider strategy

Provider adapters should support local-first operation and explicit fallbacks. A deployment must make provider priority, privacy, cost, and failure behavior visible in configuration.

## Voice pipeline

```text
Microphone → STT → Orchestrator → LLM → TTS → audio
                                      │
                                      ├→ viseme timeline
                                      └→ emotion/gesture
```

## Avatar pipeline

The avatar is intentionally decoupled from tutoring logic. A CPU-friendly renderer can be used for development; real-time/video inference can be attached through the avatar adapter without changing the learning domain.
