"""Modelo SQLAlchemy 2.0 da tabela `cash_registers` (`payments_db`)."""

from __future__ import annotations

import uuid
from datetime import datetime

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import DateTime, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.cash_register import CashRegisterStatus


class CashRegisterModel(TenantAwareModel):
    __tablename__ = "cash_registers"

    operator_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    opening_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_balance: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[CashRegisterStatus] = mapped_column(
        Enum(CashRegisterStatus), nullable=False, default=CashRegisterStatus.OPEN
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closing_counted_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    closing_divergence: Mapped[float | None] = mapped_column(Float, nullable=True)
