"""DTOs (Pydantic v2) de Request/Response do serviço de Estoque.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from src.domain.entities.inventory_item import InventoryUnit
from src.domain.entities.stock_movement import StockMovementType

_MANUAL_MOVEMENT_TYPES = (
    StockMovementType.ENTRY,
    StockMovementType.LOSS,
    StockMovementType.RETURN,
)


class CreateInventoryItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=150)
    unit: InventoryUnit
    initial_quantity: float = Field(default=0.0, ge=0)
    minimum_quantity: float = Field(default=0.0, ge=0)
    supplier_id: uuid.UUID | None = None


class InventoryItemResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    unit: InventoryUnit
    current_quantity: float
    minimum_quantity: float
    supplier_id: uuid.UUID | None
    is_below_minimum: bool


class RegisterStockMovementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    movement_type: StockMovementType
    quantity: float = Field(..., gt=0)
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _validate_is_manual(self) -> RegisterStockMovementRequest:
        """Rejeita tipos reservados à baixa automática (`SALE_DEDUCTION`) e
        à contagem (`COUNT_ADJUSTMENT`, que usa o endpoint dedicado)."""
        if self.movement_type not in _MANUAL_MOVEMENT_TYPES:
            raise ValueError(
                f"Tipo de movimentação '{self.movement_type.value}' não pode ser registrado manualmente."
            )
        return self


class AdjustStockCountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    counted_quantity: float = Field(..., ge=0)
    reason: str | None = Field(default=None, max_length=500)


class StockMovementResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    inventory_item_id: uuid.UUID
    movement_type: StockMovementType
    quantity_delta: float
    reason: str | None
    order_id: uuid.UUID | None
    created_at: datetime


class CreateSupplierRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=150)
    contact_phone: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(default=None, max_length=150)


class SupplierResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    contact_phone: str | None
    contact_email: str | None


class RecipeItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inventory_item_id: uuid.UUID
    quantity_required: float = Field(..., gt=0)


class UpsertRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    items: list[RecipeItemRequest] = Field(..., min_length=1)


class RecipeItemResponse(BaseModel):
    inventory_item_id: uuid.UUID
    quantity_required: float


class RecipeResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    items: list[RecipeItemResponse]
