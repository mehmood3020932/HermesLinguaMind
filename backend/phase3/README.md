# Hermes LinguaMind Backend — Phase 3 (Production Ready)

## Overview
Complete production-ready backend for the Hermes LinguaMind language learning application.

## Architecture
- **20 Microservices** running on ports 8000-8019
- **FastAPI** framework with async support
- **Docker + Docker Compose** containerization
- **PostgreSQL** for relational data
- **Redis** for caching and message queuing
- **Elasticsearch** for search
- **Prometheus** for metrics
- **Kubernetes** manifests included

## Quick Start

### Option 1: Docker Compose (Recommended)
```bash
cp config/.env.example .env
# Edit .env with your credentials
docker-compose -f config/docker-compose.yml up -d
```

### Option 2: Manual Development
```bash
pip install -r requirements-phase3.txt
./scripts/start_all.sh
```

### Option 3: Kubernetes
```bash
kubectl apply -f k8s/
```

## Services
| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | Central entry point, auth, routing |
| LLM Orchestration | 8001 | Provider-abstracted AI with fallback |
| TTS | 8002 | Text-to-speech with emotion |
| STT | 8003 | Speech-to-text (Whisper) |
| Viseme | 8004 | Lip-sync timeline generation |
| Pronunciation | 8005 | Phoneme-level scoring |
| Coin Ledger | 8006 | Server-authoritative economy |
| Curriculum | 8007 | SM-2 spaced repetition |
| Memory | 8008 | Long-term conversation memory |
| Moderation | 8009 | Content safety filtering |
| Grammar Rule DB | 8010 | Structured grammar rules |
| Content Generation | 8011 | Batch AI content creation |
| Personalization | 8012 | Learning style inference |
| Gesture/Emotion | 8013 | Character animation cues |
| Leaderboard | 8014 | Rankings and leagues |
| Social Exchange | 8015 | Language partner matching |
| Anti-Fraud | 8016 | Anomaly detection |
| Live Conversation | 8017 | WebRTC call mode |
| Observability | 8018 | Metrics and monitoring |
| Security | 8019 | Audit, backup, compliance |

## Testing
```bash
pytest tests/test_phase3_complete.py -v
```

## Documentation
- API Docs: `docs/API.md`
- Build Ledger: `BUILD_LEDGER.md`

## License
Proprietary — Hermes LinguaMind Project
