"""Modelo SQLAlchemy 2.0 da tabela `coupons` (`marketing_db`)."""

from __future__ import annotations

from datetime import datetime

from restaurant_database import TenantAwareModel
from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.coupon import DiscountType


class CouponModel(TenantAwareModel):
    __tablename__ = "coupons"

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    discount_type: Mapped[DiscountType] = mapped_column(Enum(DiscountType), nullable=False)
    discount_value: Mapped[float] = mapped_column(Float, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    times_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
