"""Pacote de infraestrutura de banco de dados: engine assíncrona, modelos base e repositório genérico."""

from restaurant_core.ids import generate_uuid7

from restaurant_database.base import BaseDBModel, TenantAwareModel
from restaurant_database.guid import GUID
from restaurant_database.repository import SQLAlchemyRepository
from restaurant_database.session import DatabaseManager

__all__ = [
    "GUID",
    "BaseDBModel",
    "DatabaseManager",
    "SQLAlchemyRepository",
    "TenantAwareModel",
    "generate_uuid7",
]
