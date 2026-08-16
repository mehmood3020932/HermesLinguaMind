$ErrorActionPreference = 'Stop'
Write-Host "Hermes LinguaMind Windows bootstrap" -ForegroundColor Cyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is required." }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Warning "Docker CLI not found. Install Docker Desktop or Docker Engine/WSL2 before continuing."
}

if (-not (Test-Path "backend/.env")) {
  Copy-Item "backend/.env.example" "backend/.env"
  Write-Host "Created backend/.env from .env.example. Review secrets before starting." -ForegroundColor Yellow
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
  docker compose -f backend/docker-compose.yml config | Out-Null
  Write-Host "Docker Compose configuration: OK" -ForegroundColor Green
}

Write-Host "Next: docker compose -f backend/docker-compose.yml up --build" -ForegroundColor Green
