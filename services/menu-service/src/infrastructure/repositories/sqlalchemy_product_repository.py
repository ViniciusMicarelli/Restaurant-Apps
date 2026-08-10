"""Implementação concreta de `ProductRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.product import Product
from src.infrastructure.models.product_model import ProductModel


def _to_entity(model: ProductModel) -> Product:
    return Product(
        id=model.id,
        tenant_id=model.tenant_id,
        category_id=model.category_id,
        name=model.name,
        description=model.description,
        price=model.price,
        cost_price=model.cost_price,
        tax_rate=model.tax_rate,
        photo_url=model.photo_url,
        display_order=model.display_order,
        is_active=model.is_active,
    )


class SQLAlchemyProductRepository(SQLAlchemyRepository[ProductModel]):
    model = ProductModel

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        model = await super().get_model_by_id(product_id)
        return _to_entity(model) if model is not None else None

    async def list_all(self, *, limit: int = 1000, offset: int = 0) -> list[Product]:
        models = await super().list_models(limit=limit, offset=offset)
        return [_to_entity(m) for m in models]

    async def list_by_category(self, category_id: uuid.UUID) -> list[Product]:
        stmt = select(ProductModel).where(
            ProductModel.tenant_id == self._tenant_id,
            ProductModel.category_id == category_id,
            ProductModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def add(self, product: Product) -> Product:
        model = ProductModel(
            id=product.id,
            tenant_id=product.tenant_id,
            category_id=product.category_id,
            name=product.name,
            description=product.description,
            price=product.price,
            cost_price=product.cost_price,
            tax_rate=product.tax_rate,
            photo_url=product.photo_url,
            display_order=product.display_order,
            is_active=product.is_active,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, product: Product) -> Product:
        model = await self._session.get(ProductModel, product.id)
        if model is None:
            msg = f"Produto '{product.id}' não encontrado para atualização."
            raise LookupError(msg)

        model.name = product.name
        model.description = product.description
        model.price = product.price
        model.cost_price = product.cost_price
        model.tax_rate = product.tax_rate
        model.photo_url = product.photo_url
        model.display_order = product.display_order
        model.is_active = product.is_active

        saved = await super().save_model(model)
        return _to_entity(saved)
