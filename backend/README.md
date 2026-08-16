# LinguaMax / Hermes — Consolidated Backend (Phase 3 + Phase 4)

This is a merged, wired-up version of the two phases found in the original
upload. **Read this file fully before deploying** — it tells you exactly
what is real, what was fixed, and what still needs your input before this
is a genuine production system.

## What changed from the original upload

1. **Removed 19 fake stub services** that lived under `phase4/services/`.
   They only returned hardcoded dummy JSON (e.g. TTS always "returned" the
   same fake file path, no matter what you sent it) and duplicated services
   that already have real implementations in `phase3/services/`. Keeping
   both would have meant the new orchestrator silently talked to fakes
   instead of the real engines.
2. **Kept the real Phase 3 services** (`phase3/services/*`) untouched —
   these have actual business logic (STT, TTS, pronunciation scoring, coin
   ledger, security, LLM orchestration, etc.), not stubs.
3. **Kept the real Phase 4 addition** — `hermes_orchestrator` (intent
   classification → task planning → execution → self-QA verification),
   which is genuine, substantial code (600+ lines, not a stub).
4. **Fixed the wiring**: the orchestrator's HTTP adapters and the API
   gateway's service registry were hardcoded to `localhost`, which does
   **not** work across separate Docker containers. Both now resolve
   downstream services through environment variables that default to the
   correct Docker Compose service hostnames (e.g. `http://tts:8002`).
5. **Added the missing pieces for `hermes_orchestrator` to actually build**:
   a `Dockerfile`, a trimmed `requirements-orchestrator.txt`, and a service
   block in `docker-compose.yml` (port 8020, wired to all 19 downstream
   services + the gateway).
6. **Added a `/v1/chat` convenience route** on the API Gateway that proxies
   to the orchestrator's `/v1/orchestrate` endpoint (the generic
   `/v1/{service}/{path}` proxy also reaches it at
   `/v1/hermes_orchestrator/orchestrate`).
7. Single `docker-compose.yml` at the project root now brings up **all 21
   services + Postgres + Redis + Elasticsearch + Ollama + Celery** together.

## Honest status — what is verified vs. not

**Verified in this pass (static checks only — no Docker daemon or network
access was available in the environment that prepared this zip):**
- Every one of the ~150 Python files compiles cleanly (`py_compile` — no
  syntax errors).
- `docker-compose.yml` is valid YAML; every `build.dockerfile` path it
  references actually exists on disk.
- All import names the orchestrator pulls from `phase4/shared` (models,
  auth helpers) exist with matching signatures in that same shared module.
- Service-to-service URLs in the gateway and orchestrator now match the
  actual Docker Compose service/container names.

**NOT verified — you must do this before calling it production:**
- **`docker compose build` / `docker compose up` has not actually been run
  end-to-end.** Compiling Python syntax is not the same as a working
  runtime — dependency resolution conflicts, missing system libraries (some
  services use `torch`, `whisper`, `aiortc`), or first-run migration issues
  can still surface. Run it yourself and watch the logs; I cannot guarantee
  a "zero-error" first boot for a stack this size without actually
  executing it.
- **No external API keys are included or valid** (LLM provider, TTS/STT
  engines if you use hosted ones, S3, etc.). Anything in `phase3/services/*`
  that calls a third-party API will only be "real" once you supply real
  credentials in `.env`.
- **`SECRET_KEY`, database password, and all other secrets in
  `.env.example` are placeholders.** Generate real ones before deploying
  anywhere reachable from the internet.
- No load testing, penetration testing, or security audit has been done.
  "Enterprise production ready" is a claim that requires that kind of
  testing — I have not run it, so I'm not making that claim for you.
- `phase3/services/pronunciation` still has a documented gap around forced
  phoneme alignment (see that service's code comments) — it wasn't part of
  this pass; flag if you want it addressed next.

## About `phase2/`

The upload also contained a `phase2/` directory — an **earlier iteration**
of 8 of these services (grammar_rule_db, content_generation,
personalization, gesture_emotion, leaderboard, social_exchange,
anti_fraud, live_conversation), written before the Phase 3 versions that
are actually wired into `docker-compose.yml`. Both versions are genuine,
non-stub code — Phase 2's versions are actually more elaborate for some
services — but they are two different design iterations of the same
service, not complementary. **`phase2/` is not part of the running
system in this zip** and is left untouched purely for reference.

Do **not** run `phase2/config/docker-compose.yml` — it defines the same
service names on the same ports (8010–8017) as the root `docker-compose.yml`
and will conflict. If you'd rather run the Phase 2 versions of those 8
services instead of the Phase 3 versions (or merge the best of both), tell
me and I'll rebuild the compose file around that choice — that's a real
design decision, not something I should silently pick for you.



```bash
cp .env.example .env
# edit .env — set SECRET_KEY, DATABASE_PASSWORD, and any API keys you have

docker compose build
docker compose up -d

curl http://localhost:8000/health          # API gateway
curl http://localhost:8020/health          # Hermes orchestrator
```

## Layout

```
docker-compose.yml     # single compose file, all 21 services + infra
.env.example           # copy to .env and fill in real secrets
phase3/                # real microservices (STT, TTS, coin ledger, etc.) — this is what runs
phase4/                # hermes_orchestrator (intent/plan/execute/verify)
phase2/                # legacy iteration of 8 services — NOT wired in, reference only
```

If something in here doesn't run cleanly on your machine, tell me the exact
error from `docker compose up` and I'll fix that specific failure — that's
a much more reliable way to get to "actually works" than a blind claim of
100%.
