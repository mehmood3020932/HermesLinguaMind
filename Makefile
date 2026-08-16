SHELL := /bin/bash

.PHONY: help setup up down logs doctor test backend-test mobile-analyze format clean

help:
	@echo "Hermes LinguaMind developer commands"
	@echo "  make setup          Prepare environment templates"
	@echo "  make up             Start Docker development stack"
	@echo "  make down           Stop Docker stack"
	@echo "  make logs           Follow backend logs"
	@echo "  make doctor         Run repository sanity checks"
	@echo "  make test           Run backend tests and Flutter analysis when available"
	@echo "  make backend-test   Run Python tests"
	@echo "  make mobile-analyze Run Flutter analyze"
	@echo "  make format        Format Flutter/Dart code when Flutter is installed"

setup:
	@test -f backend/.env || cp backend/.env.example backend/.env
	@echo "Environment template ready. Review backend/.env before use."

up:
	cd backend && docker compose up --build

down:
	cd backend && docker compose down

logs:
	cd backend && docker compose logs -f --tail=200

doctor:
	bash scripts/repo_doctor.sh

backend-test:
	cd backend && python -m pytest phase3/tests phase4/tests -q

mobile-analyze:
	cd mobile_app && flutter analyze

test:
	$(MAKE) doctor
	$(MAKE) backend-test
	@if command -v flutter >/dev/null 2>&1; then $(MAKE) mobile-analyze; else echo "Flutter not installed; skipping mobile analysis."; fi

format:
	@if command -v dart >/dev/null 2>&1; then cd mobile_app && dart format lib test; else echo "Dart not installed; skipping format."; fi

clean:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .dart_tool \) -prune -exec rm -rf {} +
