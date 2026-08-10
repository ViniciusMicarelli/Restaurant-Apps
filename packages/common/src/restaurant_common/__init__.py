"""Pacote comum: settings base, DTOs compartilhados, paginação e RFC 7807."""

from restaurant_common.dtos import HealthResponse, TenantContextDTO
from restaurant_common.pagination import PaginatedResponse
from restaurant_common.problem_details import ProblemDetails, register_exception_handlers
from restaurant_common.settings import (
    BaseAppSettings,
    DatabaseSettings,
    RabbitMQSettings,
    RedisSettings,
    build_settings_config,
)

__all__ = [
    "BaseAppSettings",
    "DatabaseSettings",
    "HealthResponse",
    "PaginatedResponse",
    "ProblemDetails",
    "RabbitMQSettings",
    "RedisSettings",
    "TenantContextDTO",
    "build_settings_config",
    "register_exception_handlers",
]
