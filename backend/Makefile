# Hermes LinguaMind — One-click operations
# Usage: make setup | make up | make down | make health

COMPOSE ?= docker compose
ENV_FILE ?= .env

.PHONY: help setup env build up down restart logs health ps clean validate

help:
	@echo "Hermes LinguaMind targets:"
	@echo "  make setup      - Create .env, build the image, start the stack"
	@echo "  make up         - Build + start (postgres, redis, elasticsearch, ollama, hermes_backend, nginx)"
	@echo "  make down       - Stop and remove containers"
	@echo "  make health     - Hit nginx /health and the backend's deep health"
	@echo "  make logs       - Follow hermes_backend + nginx logs"
	@echo "  make clean      - down -v (DESTROYS volumes, including the downloaded local LLM)"
	@echo "  make validate   - docker compose config check"

env:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		cp .env.example "$(ENV_FILE)"; \
		echo "Created $(ENV_FILE) from .env.example — edit secrets before production."; \
	else \
		echo "$(ENV_FILE) already exists."; \
	fi

setup: env build up health
	@echo ""
	@echo "✓ Hermes LinguaMind is up"
	@echo "  Public:   http://localhost/"
	@echo "  Backend:  http://localhost:8080/docs"
	@echo "  Health:   http://localhost/health"
	@echo "  Registry: http://localhost:8080/v1/services"

build:
	$(COMPOSE) --env-file $(ENV_FILE) build

up: env
	$(COMPOSE) --env-file $(ENV_FILE) up -d --build
	@echo "Waiting for hermes_backend (this pulls the local LLM on first run — can take a few minutes)..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12; do \
		if curl -fsS http://localhost:8080/health >/dev/null 2>&1; then \
			echo "hermes_backend healthy."; exit 0; \
		fi; \
		sleep 10; \
	done; \
	echo "Not healthy yet — check: make logs"; exit 0

down:
	$(COMPOSE) --env-file $(ENV_FILE) down

restart:
	$(COMPOSE) --env-file $(ENV_FILE) restart

logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f hermes_backend nginx

ps:
	$(COMPOSE) --env-file $(ENV_FILE) ps

health:
	@echo "=== nginx /health ==="
	@curl -fsS http://localhost/health | python3 -m json.tool || curl -fsS http://localhost:8080/health | python3 -m json.tool
	@echo ""
	@echo "=== backend /v1/services (count) ==="
	@curl -fsS http://localhost:8080/v1/services | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('count'), 'services')"
	@echo ""
	@echo "=== deep health (all 22 upstream services) ==="
	@curl -fsS "http://localhost:8080/health?deep=true" | python3 -m json.tool | head -80

validate:
	$(COMPOSE) --env-file $(ENV_FILE) config >/dev/null
	@echo "docker-compose.yml: OK"

clean:
	$(COMPOSE) --env-file $(ENV_FILE) down -v --remove-orphans
	@echo "Volumes removed (including the local LLM — it will re-download on next 'make up')."
