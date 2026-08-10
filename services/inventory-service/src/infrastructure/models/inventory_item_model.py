"""Modelo SQLAlchemy 2.0 da tabela `inventory_items` (`inventory_db`)."""

from __future__ import annotations

import uuid

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.inventory_item import InventoryUnit


class InventoryItemModel(TenantAwareModel):
    __tablename__ = "inventory_items"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    unit: Mapped[InventoryUnit] = mapped_column(Enum(InventoryUnit), nullable=False)
    current_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    minimum_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
