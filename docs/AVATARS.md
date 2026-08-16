# Avatar Architecture & Real Inference Guide

## Important distinction

Hermes contains avatar integration plumbing, but the repository does **not** claim to bundle production-grade proprietary or GPU-heavy avatar model weights. OpenTalking is an optional upstream integration.

## Modes

### Mode A — lightweight / CPU-first

Use the Flutter companion renderer, viseme timelines, emotion states, and pre-created animation assets. This is the recommended baseline for low-cost development.

### Mode B — real talking-head inference

Provision a compatible OpenTalking inference backend and connect it through the avatar API/WebRTC path. The exact model depends on GPU memory, latency requirements, output quality, and license.

### Mode C — cloud inference

A future adapter can point to a hosted provider. This should remain optional so the core project can run locally.

## Production checklist

- [ ] Select a model whose license permits the intended use.
- [ ] Confirm avatar/source media rights.
- [ ] Measure latency on the target GPU.
- [ ] Add TURN infrastructure for difficult WebRTC networks.
- [ ] Add reconnect/fallback behavior.
- [ ] Cap concurrent inference jobs.
- [ ] Monitor GPU memory and queue depth.
- [ ] Never expose internal model/worker endpoints directly to the public internet.

## OpenTalking setup

The backend includes `scripts/setup_opentalking.sh` and an optional Compose profile. Follow the upstream OpenTalking project documentation for model-specific dependencies and licensing, then enable the avatar profile.

```bash
cd backend
./scripts/setup_opentalking.sh
OPENTALKING_INFERENCE_MOCK=1 docker compose --profile avatar up --build
```

The mock profile verifies integration plumbing. It is **not** a photorealistic avatar.

For real inference, set the appropriate model/runtime configuration only after provisioning compatible model assets and a suitable GPU host.
