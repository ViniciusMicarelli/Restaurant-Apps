"""Modelo SQLAlchemy 2.0 da tabela `categories` (`menu_db`)."""

from __future__ import annotations

from restaurant_database import TenantAwareModel
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class CategoryModel(TenantAwareModel):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
