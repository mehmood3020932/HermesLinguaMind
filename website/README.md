# Hermes LinguaMind Web Experience

Production-oriented, dependency-free marketing + live gateway experience for Hermes LinguaMind.

## Runtime integration

When deployed through the repository's nginx container, the website is served at `/` and calls the same-origin Hermes gateway:

- `GET /health`
- `GET /v1/services`
- `POST /v1/chat`
- `GET /docs`

No API key is embedded in the browser. Configure provider secrets only on the backend.

For local static preview without the backend:

```bash
python -m http.server 8088 -d website
```

The visual site still renders, but the live tutor/health panel requires the Hermes backend to be reachable from the browser origin.
