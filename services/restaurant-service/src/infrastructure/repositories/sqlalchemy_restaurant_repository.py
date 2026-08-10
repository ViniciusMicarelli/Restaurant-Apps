"""Implementação concreta de `RestaurantRepositoryInterface` sobre SQLAlchemy 2.0 Async.

Não estende `restaurant_database.SQLAlchemyRepository` (que é tenant-scoped
por design, ligado a `TenantAwareModel`) — `RestaurantModel` não tem
`tenant_id` porque cada linha É um tenant.
"""

from __future__ import annotations

import uuid

from restaurant_core.exceptions import OptimisticLockException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError
from src.domain.entities.restaurant import Restaurant, RestaurantBranding
from src.infrastructure.models.restaurant_model import RestaurantModel


def _to_entity(model: RestaurantModel) -> Restaurant:
    return Restaurant(
        id=model.id,
        slug=model.slug,
        trade_name=model.trade_name,
        legal_name=model.legal_name,
        cnpj=model.cnpj,
        phone=model.phone,
        currency=model.currency,
        service_fee_percent=model.service_fee_percent,
        is_active=model.is_active,
        branding=RestaurantBranding(**model.branding) if model.branding else RestaurantBranding(),
    )


class SQLAlchemyRestaurantRepository:
    """Repositório de `Restaurant`, escopado apenas por `deleted_at IS NULL` (sem tenant)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, restaurant_id: uuid.UUID) -> Restaurant | None:
        stmt = select(RestaurantModel).where(
            RestaurantModel.id == restaurant_id, RestaurantModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_slug(self, slug: str) -> Restaurant | None:
        stmt = select(RestaurantModel).where(
            RestaurantModel.slug == slug, RestaurantModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def slug_exists(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None

    async def add(self, restaurant: Restaurant) -> Restaurant:
        model = RestaurantModel(
            id=restaurant.id,
            slug=restaurant.slug,
            trade_name=restaurant.trade_name,
            legal_name=restaurant.legal_name,
            cnpj=restaurant.cnpj,
            phone=restaurant.phone,
            currency=restaurant.currency,
            service_fee_percent=restaurant.service_fee_percent,
            is_active=restaurant.is_active,
            branding=vars(restaurant.branding),
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def save(self, restaurant: Restaurant) -> Restaurant:
        stmt = select(RestaurantModel).where(RestaurantModel.id == restaurant.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.trade_name = restaurant.trade_name
        model.phone = restaurant.phone
        model.currency = restaurant.currency
        model.service_fee_percent = restaurant.service_fee_percent
        model.is_active = restaurant.is_active
        model.branding = vars(restaurant.branding)

        try:
            await self._session.flush()
        except StaleDataError as exc:
            raise OptimisticLockException("Restaurant") from exc

        return _to_entity(model)
