# Hermes Web Production

## User-facing surface

Nginx serves `backend/frontend/` at `/`. The web experience is dependency-free and includes:

- premium responsive landing page
- product/architecture storytelling
- GitHub/community conversion paths
- PWA manifest + service worker shell caching
- live backend health indicator
- live service registry count
- live tutor chat through `POST /v1/chat`
- same-origin API calls so no browser-side secret is required

## Runtime flow

```text
Browser
  │
  ▼
Nginx :80
  ├── static website → /usr/share/nginx/html/app
  ├── /health → Hermes gateway
  ├── /v1/* → Hermes gateway
  ├── /svc/* → Hermes gateway
  └── /avatar-api/* → optional OpenTalking API
```

## Local verification

```bash
cd backend
cp .env.example .env
# review secrets

docker compose config

docker compose up --build -d
curl -fsS http://localhost/health
curl -fsS http://localhost/v1/services
curl -fsS http://localhost/ | head
```

The live tutor panel should only be called “online” when the backend health endpoint is reachable. The website deliberately does not fabricate AI responses if the API is down.
