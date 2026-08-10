"""Modelo SQLAlchemy 2.0 da tabela `recipes` (`inventory_db`).

Os insumos (`RecipeItem`) são armazenados como JSON embutido — sempre lidos
e escritos junto com a ficha técnica como um todo (agregado único), sem
necessidade de consulta relacional independente sobre insumos.
"""

from __future__ import annotations

import uuid
from typing import Any

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column


class RecipeModel(TenantAwareModel):
    __tablename__ = "recipes"

    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, unique=True, index=True)
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
