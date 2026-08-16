# Hermes LinguaMind API Documentation

## Base URLs
- API Gateway: `http://localhost:8000`
- All services accessible via `/v1/{service}/{endpoint}`

## Authentication
All endpoints require Bearer token authentication except `/health` and `/v1/auth/*`.

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/v1/auth/me
```

## Services

### 1. API Gateway (Port 8000)
- `POST /v1/auth/register` - User registration
- `POST /v1/auth/login` - User login
- `POST /v1/auth/refresh` - Refresh token
- `GET /v1/auth/me` - Get current user
- `GET /v1/services` - List all services
- `GET /v1/rate-limit` - Rate limit info

### 2. LLM Orchestration (Port 8001)
- `POST /v1/generate` - Generate text
- `POST /v1/grammar-check` - Check grammar
- `POST /v1/conversation` - Conversational AI
- `GET /v1/providers` - List LLM providers

### 3. TTS (Port 8002)
- `POST /v1/synthesize` - Text to speech
- `GET /v1/engines` - List TTS engines

### 4. STT (Port 8003)
- `POST /v1/transcribe` - Speech to text
- `GET /v1/models` - List STT models

### 5. Viseme (Port 8004)
- `POST /v1/generate` - Generate viseme timeline
- `GET /v1/viseme-map` - Get viseme mappings

### 6. Pronunciation (Port 8005)
- `POST /v1/score` - Score pronunciation
- `GET /v1/calibration` - Calibration info

### 7. Coin Ledger (Port 8006)
- `POST /v1/transaction` - Create transaction
- `GET /v1/balance/{user_id}` - Get balance
- `GET /v1/transactions/{user_id}` - Get transactions
- `POST /v1/reconcile` - Reconcile ledger

### 8. Curriculum (Port 8007)
- `POST /v1/curriculum` - Get curriculum
- `POST /v1/complete-lesson` - Complete lesson
- `GET /v1/review-queue/{user_id}` - Get review queue

### 9. Memory (Port 8008)
- `POST /v1/store` - Store memory
- `GET /v1/retrieve/{user_id}` - Retrieve memories
- `POST /v1/summarize/{user_id}` - Summarize memories

### 10. Moderation (Port 8009)
- `POST /v1/moderate` - Moderate content
- `POST /v1/batch-moderate` - Batch moderation
- `GET /v1/policies` - Get policies

### 11. Grammar Rule DB (Port 8010)
- `GET /v1/rules` - List grammar rules
- `POST /v1/verify` - Verify grammar
- `POST /v1/rules` - Add rule

### 12. Content Generation (Port 8011)
- `POST /v1/generate` - Generate content
- `GET /v1/content` - List generated content

### 13. Personalization (Port 8012)
- `POST /v1/analyze` - Analyze user
- `GET /v1/profile/{user_id}` - Get profile

### 14. Gesture/Emotion (Port 8013)
- `POST /v1/gesture` - Get gesture cue
- `GET /v1/gestures` - List gestures

### 15. Leaderboard (Port 8014)
- `POST /v1/leaderboard` - Get leaderboard
- `POST /v1/submit-score` - Submit score

### 16. Social Exchange (Port 8015)
- `POST /v1/match` - Find language exchange partners
- `POST /v1/profile` - Update social profile
- `POST /v1/report` - Report user

### 17. Anti-Fraud (Port 8016)
- `POST /v1/check` - Check for fraud
- `GET /v1/alerts` - Get fraud alerts

### 18. Live Conversation (Port 8017)
- `POST /v1/start` - Start conversation
- `WS /v1/ws/{session_id}` - WebSocket endpoint
- `POST /v1/end/{session_id}` - End conversation
- `GET /v1/benchmark` - Latency benchmark

### 19. Observability (Port 8018)
- `POST /v1/metrics/ingest` - Ingest metrics
- `GET /v1/metrics/{service}` - Get service metrics
- `GET /v1/metrics/all` - Get all metrics
- `GET /v1/alerts` - Get alerts
- `GET /v1/prometheus` - Prometheus metrics
- `GET /v1/dashboard` - Dashboard summary

### 20. Security (Port 8019)
- `POST /v1/audit/log` - Log audit event
- `GET /v1/audit/logs` - Get audit logs
- `POST /v1/backup` - Create backup
- `GET /v1/backups` - List backups
- `POST /v1/scan` - Security scan
- `POST /v1/secrets/rotate` - Rotate secrets
- `GET /v1/compliance/status` - Compliance status
