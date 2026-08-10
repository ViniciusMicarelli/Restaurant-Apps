"""Modelo SQLAlchemy 2.0 da tabela `stock_movements` (`inventory_db`) — auditoria append-only."""

from __future__ import annotations

import uuid

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.stock_movement import StockMovementType


class StockMovementModel(TenantAwareModel):
    __tablename__ = "stock_movements"

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    movement_type: Mapped[StockMovementType] = mapped_column(
        Enum(StockMovementType), nullable=False
    )
    quantity_delta: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
