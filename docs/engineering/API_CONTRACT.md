# API Contract

This document defines the intended public contract. Internal service boundaries may change without breaking clients.

## Core resources

| Resource | Purpose |
|---|---|
| `/health` | Liveness/readiness information |
| `/auth/*` | Authentication and account recovery |
| `/profile` | Native language, target language, level, preferences |
| `/lessons/*` | Curriculum and lesson sessions |
| `/tutor/*` | Text/voice tutoring interactions |
| `/speech/*` | STT/TTS and pronunciation workflows |
| `/progress/*` | Mastery, streaks and lesson history |
| `/companions/*` | Companion catalog and session state |
| `/social/*` | Community and language exchange features |

## Request invariants

Every authenticated request should carry:

- `Authorization`
- `X-Request-ID`
- optional locale and timezone metadata

## Tutor request model

```json
{
  "native_language": "ur",
  "target_language": "en",
  "level": "A1",
  "mode": "conversation",
  "message": "I want to practice ordering food",
  "session_id": "..."
}
```

The server should resolve the language policy from the user profile rather than trusting arbitrary client-side model/provider choices.

## Compatibility rules

- Add fields without removing existing fields in a minor release.
- Deprecate before removal.
- Return stable machine-readable error codes.
- Never expose provider secrets, internal stack traces or database errors to clients.
