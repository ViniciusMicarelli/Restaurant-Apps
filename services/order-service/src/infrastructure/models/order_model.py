"""Modelo SQLAlchemy 2.0 da tabela `orders` (`orders_db`).

Os itens (`OrderItem`) são armazenados como JSON embutido — são sempre lidos
e escritos junto com o pedido como um todo (agregado único), sem necessidade
de consulta relacional independente sobre itens nesta fase.
"""

from __future__ import annotations

import uuid
from typing import Any

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import JSON, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.order import OrderStatus, OrderType


class OrderModel(TenantAwareModel):
    __tablename__ = "orders"

    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    table_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    command_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING
    )
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
