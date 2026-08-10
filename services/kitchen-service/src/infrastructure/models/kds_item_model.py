"""Modelo SQLAlchemy 2.0 da tabela `kds_items` (`kitchen_db`)."""

from __future__ import annotations

import uuid
from datetime import datetime

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.kds_item import KDSItemStatus, KDSStation


class KDSItemModel(TenantAwareModel):
    __tablename__ = "kds_items"

    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    station: Mapped[KDSStation] = mapped_column(
        Enum(KDSStation), nullable=False, default=KDSStation.COZINHA_QUENTE
    )
    table_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[KDSItemStatus] = mapped_column(
        Enum(KDSItemStatus), nullable=False, default=KDSItemStatus.PENDING
    )
    # Base do SLA de cozinha no dashboard do dono (docs/logs/2026-08-06.md):
    # `created_at` (herdado de `TenantAwareModel`) → `ready_at` é o tempo de
    # preparo; `delivered_at` fecha o ciclo até a entrega.
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
