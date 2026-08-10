"""Modelo SQLAlchemy 2.0 da tabela `deliveries` (`delivery_db`)."""

from __future__ import annotations

import uuid

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.delivery import DeliveryStatus


class DeliveryModel(TenantAwareModel):
    __tablename__ = "deliveries"

    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)
    courier_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus), nullable=False, default=DeliveryStatus.PENDING
    )
