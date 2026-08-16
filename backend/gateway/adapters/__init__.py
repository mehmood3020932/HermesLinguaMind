"""Service-proxy adapters package."""

from gateway.adapters.proxy import mount_all_service_proxies, check_upstream_health
from gateway.adapters.registry import SERVICE_REGISTRY, REGISTRY_BY_NAME, services_by_tier

__all__ = [
    "SERVICE_REGISTRY",
    "REGISTRY_BY_NAME",
    "services_by_tier",
    "mount_all_service_proxies",
    "check_upstream_health",
]
