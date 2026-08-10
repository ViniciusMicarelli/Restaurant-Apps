"""Modelo SQLAlchemy 2.0 da tabela `commands` (comandas, `dining_db`)."""

from __future__ import annotations

import uuid
from datetime import datetime

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.command import CommandStatus


class CommandModel(TenantAwareModel):
    __tablename__ = "commands"

    table_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    waiter_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    customer_cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
    status: Mapped[CommandStatus] = mapped_column(
        Enum(CommandStatus), nullable=False, default=CommandStatus.OPEN
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    service_fee_charged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
