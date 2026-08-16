# Hermes LinguaMind — End-to-End Product Map

Hermes is a single repository containing the public website, Flutter mobile client, unified backend gateway, AI orchestration, voice stack, learning services, optional avatar stack, infrastructure, CI, and contributor tooling.

## One product, three clients/layers

```text
                         ┌──────────────────────────┐
                         │   Hermes Public Website  │
                         │  marketing + live tutor  │
                         └────────────┬─────────────┘
                                      │ same-origin /v1
                         ┌────────────▼─────────────┐
                         │        NGINX :80         │
                         │ static app + API gateway │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │   Unified Hermes Gateway │
                         │ health / registry / chat│
                         └────────────┬─────────────┘
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                        │
              ▼                       ▼                        ▼
        AI orchestration         Voice pipeline          Learning state
        LLM + memory             STT + TTS + viseme      curriculum + progress
              │                       │                        │
              └───────────────────────┼────────────────────────┘
                                      ▼
                             Companion / Avatar
                                      │
                      ┌───────────────┴──────────────┐
                      ▼                              ▼
                 CPU companion                 OpenTalking path
                 always available             optional GPU/model stack

Flutter mobile app ───────────────► same /v1 gateway
```

## Golden user journey

1. Choose native language.
2. Choose target language.
3. Choose level and learning goal.
4. Meet a companion.
5. Start a text or voice lesson.
6. Hermes explains difficult concepts in the learner's native language.
7. Hermes switches to the target language for practice.
8. STT transcribes spoken input.
9. AI evaluates intent, grammar, pronunciation and lesson state.
10. TTS produces the tutor response.
11. Visemes/emotion drive the companion presentation layer.
12. Progress and memory are persisted.

## Runtime truth

- The public website uses real same-origin API calls; it does not fabricate tutor responses when the backend is unavailable.
- The default avatar path is lightweight and does not imply proprietary photorealistic model weights are bundled.
- OpenTalking is optional and must be provisioned separately with its model/runtime requirements.
- Production certification requires a real deployment test on the target hardware.

## Release gates

A release is ready only when all applicable gates pass:

- `make doctor`
- backend unit/integration tests
- `flutter analyze` and `flutter test`
- `docker compose config`
- image build
- gateway `/health`
- gateway `/v1/services`
- website live-tutor request
- mobile login/session smoke test
- security scan
- secret scan
- backup/restore rehearsal for production

See `docs/PRODUCTION_GATE.md`.
