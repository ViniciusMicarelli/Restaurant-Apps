"""Caso de uso: cadastro de um novo fornecedor de insumos."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from src.application.dtos.inventory_dtos import SupplierResponse
from src.application.interfaces.repository_interface import SupplierRepositoryInterface
from src.application.use_cases._shared import to_supplier_response
from src.domain.entities.supplier import Supplier


@dataclass
class CreateSupplierUseCase:
    supplier_repository: SupplierRepositoryInterface

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        name: str,
        contact_phone: str | None,
        contact_email: str | None,
    ) -> SupplierResponse:
        supplier = Supplier(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            name=name,
            contact_phone=contact_phone,
            contact_email=contact_email,
        )
        created = await self.supplier_repository.add(supplier)
        return to_supplier_response(created)


@dataclass
class ListSuppliersUseCase:
    supplier_repository: SupplierRepositoryInterface

    async def execute(self) -> list[SupplierResponse]:
        suppliers = await self.supplier_repository.list_all()
        return [to_supplier_response(s) for s in suppliers]
