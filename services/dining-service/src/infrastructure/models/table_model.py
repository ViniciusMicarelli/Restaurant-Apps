"""Modelo SQLAlchemy 2.0 da tabela `tables` (`dining_db`)."""

from __future__ import annotations

from datetime import datetime

from restaurant_database import TenantAwareModel
from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.table import TableStatus


class TableModel(TenantAwareModel):
    __tablename__ = "tables"

    number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TableStatus] = mapped_column(
        Enum(TableStatus), nullable=False, default=TableStatus.AVAILABLE
    )
    qr_code_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    active_qr_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    qr_secret_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
