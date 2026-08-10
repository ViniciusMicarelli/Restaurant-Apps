"""Modelo SQLAlchemy 2.0 da tabela `addon_groups` (`menu_db`).

As opções (`AddonOption`) são armazenadas como JSON embutido — não há
consulta relacional independente sobre elas, então uma tabela própria
adicionaria complexidade sem benefício nesta fase.
"""

from __future__ import annotations

import uuid
from typing import Any

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class AddonGroupModel(TenantAwareModel):
    __tablename__ = "addon_groups"

    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_selections: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_selections: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
