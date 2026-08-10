"""Modelo SQLAlchemy 2.0 da tabela `suppliers` (`inventory_db`)."""

from __future__ import annotations

from restaurant_database import TenantAwareModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class SupplierModel(TenantAwareModel):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
