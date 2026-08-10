"""Implementação concreta de `InventoryItemRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from src.domain.entities.inventory_item import InventoryItem
from src.infrastructure.models.inventory_item_model import InventoryItemModel


def _to_entity(model: InventoryItemModel) -> InventoryItem:
    return InventoryItem(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        unit=model.unit,
        current_quantity=model.current_quantity,
        minimum_quantity=model.minimum_quantity,
        supplier_id=model.supplier_id,
    )


class SQLAlchemyInventoryItemRepository(SQLAlchemyRepository[InventoryItemModel]):
    model = InventoryItemModel

    async def get_by_id(self, inventory_item_id: uuid.UUID) -> InventoryItem | None:
        model = await super().get_model_by_id(inventory_item_id)
        return _to_entity(model) if model is not None else None

    async def list_all(self) -> list[InventoryItem]:
        models = await super().list_models(limit=1000)
        return [_to_entity(m) for m in models]

    async def add(self, item: InventoryItem) -> InventoryItem:
        model = InventoryItemModel(
            id=item.id,
            tenant_id=item.tenant_id,
            name=item.name,
            unit=item.unit,
            current_quantity=item.current_quantity,
            minimum_quantity=item.minimum_quantity,
            supplier_id=item.supplier_id,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, item: InventoryItem) -> InventoryItem:
        model = await self._session.get(InventoryItemModel, item.id)
        if model is None:
            msg = f"Insumo '{item.id}' não encontrado para atualização."
            raise LookupError(msg)
        model.current_quantity = item.current_quantity
        model.minimum_quantity = item.minimum_quantity
        model.supplier_id = item.supplier_id
        saved = await super().save_model(model)
        return _to_entity(saved)
