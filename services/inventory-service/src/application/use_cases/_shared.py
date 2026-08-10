"""Helpers compartilhados entre casos de uso do serviço de Estoque."""

from __future__ import annotations

from src.application.dtos.inventory_dtos import (
    InventoryItemResponse,
    RecipeItemResponse,
    RecipeResponse,
    StockMovementResponse,
    SupplierResponse,
)
from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.entities.stock_movement import StockMovement
from src.domain.entities.supplier import Supplier


def to_inventory_item_response(item: InventoryItem) -> InventoryItemResponse:
    return InventoryItemResponse(
        id=item.id,
        tenant_id=item.tenant_id,
        name=item.name,
        unit=item.unit,
        current_quantity=item.current_quantity,
        minimum_quantity=item.minimum_quantity,
        supplier_id=item.supplier_id,
        is_below_minimum=item.is_below_minimum,
    )


def to_supplier_response(supplier: Supplier) -> SupplierResponse:
    return SupplierResponse(
        id=supplier.id,
        tenant_id=supplier.tenant_id,
        name=supplier.name,
        contact_phone=supplier.contact_phone,
        contact_email=supplier.contact_email,
    )


def to_recipe_response(recipe: Recipe) -> RecipeResponse:
    return RecipeResponse(
        id=recipe.id,
        tenant_id=recipe.tenant_id,
        product_id=recipe.product_id,
        items=[
            RecipeItemResponse(
                inventory_item_id=i.inventory_item_id, quantity_required=i.quantity_required
            )
            for i in recipe.items
        ],
    )


def to_stock_movement_response(movement: StockMovement) -> StockMovementResponse:
    return StockMovementResponse(
        id=movement.id,
        tenant_id=movement.tenant_id,
        inventory_item_id=movement.inventory_item_id,
        movement_type=movement.movement_type,
        quantity_delta=movement.quantity_delta,
        reason=movement.reason,
        order_id=movement.order_id,
        created_at=movement.created_at,
    )
