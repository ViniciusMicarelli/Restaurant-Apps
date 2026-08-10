"""Modelo SQLAlchemy 2.0 da tabela `restaurants` no PostgreSQL isolado (`restaurant_db`).

Não herda de `TenantAwareModel`: cada linha desta tabela É um tenant (seu
`id` é reutilizado como `tenant_id` pelos demais microsserviços).
"""

from __future__ import annotations

from typing import Any

from restaurant_database import BaseDBModel
from sqlalchemy import JSON, Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column


class RestaurantModel(BaseDBModel):
    """Mapeamento da tabela `restaurants` — herda `id`/auditoria/lock otimista de `BaseDBModel`."""

    __tablename__ = "restaurants"

    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    trade_name: Mapped[str] = mapped_column(String(150), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    service_fee_percent: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    branding: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
