"""Implementação concreta de `CouponRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.coupon import Coupon
from src.infrastructure.models.coupon_model import CouponModel


def _to_entity(model: CouponModel) -> Coupon:
    return Coupon(
        id=model.id,
        tenant_id=model.tenant_id,
        code=model.code,
        discount_type=model.discount_type,
        discount_value=model.discount_value,
        valid_from=model.valid_from,
        valid_until=model.valid_until,
        max_uses=model.max_uses,
        times_used=model.times_used,
        active=model.active,
    )


class SQLAlchemyCouponRepository(SQLAlchemyRepository[CouponModel]):
    model = CouponModel

    async def get_by_code(self, code: str) -> Coupon | None:
        stmt = select(self.model).where(
            self.model.code == code.strip().upper(),
            self.model.tenant_id == self._tenant_id,
            self.model.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_all(self) -> list[Coupon]:
        models = await super().list_models(limit=1000)
        return [_to_entity(m) for m in models]

    async def add(self, coupon: Coupon) -> Coupon:
        model = CouponModel(
            id=coupon.id,
            tenant_id=coupon.tenant_id,
            code=coupon.code,
            discount_type=coupon.discount_type,
            discount_value=coupon.discount_value,
            valid_from=coupon.valid_from,
            valid_until=coupon.valid_until,
            max_uses=coupon.max_uses,
            times_used=coupon.times_used,
            active=coupon.active,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, coupon: Coupon) -> Coupon:
        model = await self._session.get(CouponModel, coupon.id)
        if model is None:
            msg = f"Cupom '{coupon.id}' não encontrado para atualização."
            raise LookupError(msg)
        model.times_used = coupon.times_used
        model.active = coupon.active
        saved = await super().save_model(model)
        return _to_entity(saved)
