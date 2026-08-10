"""Modelo SQLAlchemy 2.0 da tabela `queue_entries` (`dining_db`)."""

from __future__ import annotations

from restaurant_database import TenantAwareModel
from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.queue_entry import QueueStatus


class QueueEntryModel(TenantAwareModel):
    __tablename__ = "queue_entries"

    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus), nullable=False, default=QueueStatus.WAITING
    )
