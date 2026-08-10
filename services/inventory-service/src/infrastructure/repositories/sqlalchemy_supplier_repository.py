"""Implementação concreta de `SupplierRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

from restaurant_database import SQLAlchemyRepository
from src.domain.entities.supplier import Supplier
from src.infrastructure.models.supplier_model import SupplierModel


def _to_entity(model: SupplierModel) -> Supplier:
    return Supplier(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        contact_phone=model.contact_phone,
        contact_email=model.contact_email,
    )


class SQLAlchemySupplierRepository(SQLAlchemyRepository[SupplierModel]):
    model = SupplierModel

    async def list_all(self) -> list[Supplier]:
        models = await super().list_models(limit=1000)
        return [_to_entity(m) for m in models]

    async def add(self, supplier: Supplier) -> Supplier:
        model = SupplierModel(
            id=supplier.id,
            tenant_id=supplier.tenant_id,
            name=supplier.name,
            contact_phone=supplier.contact_phone,
            contact_email=supplier.contact_email,
        )
        created = await super().add_model(model)
        return _to_entity(created)
