"""Pacote core compartilhado: tipos primitivos, exceções de domínio e utilitários base.

Este pacote NUNCA deve depender de FastAPI, SQLAlchemy, Redis ou qualquer
biblioteca de infraestrutura — apenas Python padrão e Pydantic.
"""

from restaurant_core.exceptions import (
    BaseDomainException,
    ForbiddenException,
    OptimisticLockException,
    ResourceNotFoundException,
    TenantIsolationException,
    UnauthorizedException,
)
from restaurant_core.ids import generate_uuid7

__all__ = [
    "BaseDomainException",
    "ForbiddenException",
    "OptimisticLockException",
    "ResourceNotFoundException",
    "TenantIsolationException",
    "UnauthorizedException",
    "generate_uuid7",
]
