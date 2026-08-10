"""Modelo SQLAlchemy 2.0 da tabela `kds_logs` (`kitchen_db`) — auditoria append-only."""

from __future__ import annotations

import uuid

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.kds_item import KDSItemStatus


class KDSLogModel(TenantAwareModel):
    __tablename__ = "kds_logs"

    kds_item_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    from_status: Mapped[KDSItemStatus] = mapped_column(Enum(KDSItemStatus), nullable=False)
    to_status: Mapped[KDSItemStatus] = mapped_column(Enum(KDSItemStatus), nullable=False)
