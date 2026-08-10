"""Modelo SQLAlchemy 2.0 da tabela `cash_movements` (`payments_db`) — auditoria append-only."""

from __future__ import annotations

import uuid

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.cash_movement import CashMovementType


class CashMovementModel(TenantAwareModel):
    __tablename__ = "cash_movements"

    cash_register_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    movement_type: Mapped[CashMovementType] = mapped_column(Enum(CashMovementType), nullable=False)
    amount_delta: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
