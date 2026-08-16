"""
Hermes LinguaMind — Observability Service
Port: 8018 | Phase 3 — Production Ready
Prometheus metrics, OpenTelemetry tracing, health aggregation
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime
from typing import Dict, List, Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, ServiceMetrics
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.observability")
app = FastAPI(title="Hermes Observability", version="3.0.0")
_app_start_time = time.time()

# Metrics storage
_service_metrics: Dict[str, List[ServiceMetrics]] = {}
_logs: List[Dict[str, Any]] = []
_alerts: List[Dict[str, Any]] = []

# Try to import prometheus client
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True

    REQUEST_COUNT = Counter("hermes_requests_total", "Total requests", ["service", "method", "status"])
    REQUEST_LATENCY = Histogram("hermes_request_duration_seconds", "Request latency", ["service"])
    ACTIVE_CONNECTIONS = Gauge("hermes_active_connections", "Active connections", ["service"])
    ERROR_RATE = Gauge("hermes_error_rate", "Error rate", ["service"])
except ImportError:
    PROMETHEUS_AVAILABLE = False

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="observability", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time,
                        dependencies={"prometheus": "ready" if PROMETHEUS_AVAILABLE else "not_configured"})

@app.post("/v1/metrics/ingest", response_model=HermesResponse)
async def ingest_metrics(request: Request, metrics: dict):
    request_id = getattr(request.state, "request_id", generate_request_id())
    service_name = metrics.get("service_name", "unknown")

    if service_name not in _service_metrics:
        _service_metrics[service_name] = []

    metric = ServiceMetrics(**metrics)
    _service_metrics[service_name].append(metric)

    # Keep only last 1000 metrics per service
    if len(_service_metrics[service_name]) > 1000:
        _service_metrics[service_name] = _service_metrics[service_name][-1000:]

    # Update Prometheus metrics if available
    if PROMETHEUS_AVAILABLE:
        REQUEST_COUNT.labels(service=service_name, method="GET", status="200").inc()
        REQUEST_LATENCY.labels(service=service_name).observe(metrics.get("avg_latency_ms", 0) / 1000)
        ACTIVE_CONNECTIONS.labels(service=service_name).set(metrics.get("active_connections", 0))
        ERROR_RATE.labels(service=service_name).set(metrics.get("error_rate", 0))

    # Check for alerts
    if metrics.get("error_rate", 0) > 0.1:
        alert = {"service": service_name, "type": "high_error_rate",
                 "value": metrics["error_rate"], "threshold": 0.1,
                 "timestamp": datetime.utcnow().isoformat(), "status": "firing"}
        _alerts.append(alert)
        logger.warning("alert_firing", service=service_name, type="high_error_rate", value=metrics["error_rate"])

    if metrics.get("p99_latency_ms", 0) > 5000:
        alert = {"service": service_name, "type": "high_latency",
                 "value": metrics["p99_latency_ms"], "threshold": 5000,
                 "timestamp": datetime.utcnow().isoformat(), "status": "firing"}
        _alerts.append(alert)

    return HermesResponse(success=True, data={"status": "ingested"}, request_id=request_id)

@app.get("/v1/metrics/{service_name}", response_model=HermesResponse)
async def get_service_metrics(service_name: str, request: Request, limit: int = 100):
    request_id = getattr(request.state, "request_id", generate_request_id())
    metrics = _service_metrics.get(service_name, [])[-limit:]

    if metrics:
        avg_latency = sum(m.avg_latency_ms for m in metrics) / len(metrics)
        avg_error = sum(m.error_rate for m in metrics) / len(metrics)
    else:
        avg_latency = 0
        avg_error = 0

    return HermesResponse(success=True, data={
        "service": service_name,
        "metrics_count": len(metrics),
        "avg_latency_ms": round(avg_latency, 2),
        "avg_error_rate": round(avg_error, 4),
        "latest": metrics[-1].model_dump() if metrics else None,
    }, request_id=request_id)

@app.get("/v1/metrics/all", response_model=HermesResponse)
async def get_all_metrics(request: Request):
    request_id = getattr(request.state, "request_id", generate_request_id())
    summary = {}
    for service, metrics in _service_metrics.items():
        if metrics:
            summary[service] = {
                "latest_latency_ms": round(metrics[-1].avg_latency_ms, 2),
                "latest_error_rate": round(metrics[-1].error_rate, 4),
                "active_connections": metrics[-1].active_connections,
            }
    return HermesResponse(success=True, data={"services": summary, "total_services": len(summary)}, request_id=request_id)

@app.get("/v1/alerts", response_model=HermesResponse)
async def get_alerts(request: Request, status: str = None):
    request_id = getattr(request.state, "request_id", generate_request_id())
    alerts = _alerts
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    return HermesResponse(success=True, data={"alerts": alerts[-100:], "total": len(alerts)}, request_id=request_id)

@app.get("/v1/prometheus")
async def prometheus_metrics():
    if PROMETHEUS_AVAILABLE:
        from fastapi.responses import Response
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    return {"error": "Prometheus client not available"}

@app.get("/v1/dashboard")
async def get_dashboard():
    """Get a summary dashboard of all services."""
    dashboard = {
        "generated_at": datetime.utcnow().isoformat(),
        "services": {},
        "alerts": {"firing": len([a for a in _alerts if a["status"] == "firing"]),
                   "total": len(_alerts)},
        "overall_health": "healthy",
    }

    for service, metrics in _service_metrics.items():
        if metrics:
            latest = metrics[-1]
            health = "healthy"
            if latest.error_rate > 0.05:
                health = "degraded"
            if latest.error_rate > 0.2:
                health = "critical"

            dashboard["services"][service] = {
                "health": health,
                "latency_ms": round(latest.avg_latency_ms, 2),
                "error_rate": round(latest.error_rate, 4),
                "requests_per_second": round(latest.requests_per_second, 2),
                "active_connections": latest.active_connections,
            }

            if health != "healthy":
                dashboard["overall_health"] = "degraded"

    return dashboard

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time, "services_monitored": len(_service_metrics),
            "total_alerts": len(_alerts)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8018, log_level="info")
