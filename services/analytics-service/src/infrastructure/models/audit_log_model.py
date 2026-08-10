"""Modelo SQLAlchemy 2.0 da tabela `audit_logs` (`analytics_db`) — append-only."""

from __future__ import annotations

import uuid
from typing import Any

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column


class AuditLogModel(TenantAwareModel):
    __tablename__ = "audit_logs"

    event_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
