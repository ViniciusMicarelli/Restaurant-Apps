"""Implementação concreta de `AddonGroupRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.addon import AddonGroup, AddonOption
from src.infrastructure.models.addon_group_model import AddonGroupModel


def _to_entity(model: AddonGroupModel) -> AddonGroup:
    return AddonGroup(
        id=model.id,
        tenant_id=model.tenant_id,
        product_id=model.product_id,
        name=model.name,
        min_selections=model.min_selections,
        max_selections=model.max_selections,
        options=[AddonOption(name=o["name"], price_delta=o["price_delta"]) for o in model.options],
    )


class SQLAlchemyAddonGroupRepository(SQLAlchemyRepository[AddonGroupModel]):
    model = AddonGroupModel

    async def list_by_product(self, product_id: uuid.UUID) -> list[AddonGroup]:
        stmt = select(AddonGroupModel).where(
            AddonGroupModel.tenant_id == self._tenant_id,
            AddonGroupModel.product_id == product_id,
            AddonGroupModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def add(self, addon_group: AddonGroup) -> AddonGroup:
        model = AddonGroupModel(
            id=addon_group.id,
            tenant_id=addon_group.tenant_id,
            product_id=addon_group.product_id,
            name=addon_group.name,
            min_selections=addon_group.min_selections,
            max_selections=addon_group.max_selections,
            options=[{"name": o.name, "price_delta": o.price_delta} for o in addon_group.options],
        )
        created = await super().add_model(model)
        return _to_entity(created)
