"""Entidades `Recipe`/`RecipeItem` — ficha técnica de produto (US-02.4).

Associa um produto do `menu-service` aos insumos do estoque necessários
para prepará-lo, habilitando a baixa automática na venda.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class RecipeItem:
    """Insumo e quantidade necessária dentro da ficha técnica de um produto."""

    inventory_item_id: uuid.UUID
    quantity_required: float

    def __post_init__(self) -> None:
        if self.quantity_required <= 0:
            raise ValueError(
                "A quantidade necessária de um insumo na ficha técnica deve ser positiva."
            )


@dataclass
class Recipe:
    """Ficha técnica de um produto do cardápio (Aggregate Root).

    Attributes:
        id: UUIDv7 da ficha técnica.
        tenant_id: ID do restaurante proprietário.
        product_id: ID do produto associado (`menu-service`).
        items: Insumos e quantidades necessárias para produzir uma unidade do produto.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    items: list[RecipeItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError("Uma ficha técnica deve conter ao menos um insumo.")

    def replace_items(self, items: list[RecipeItem]) -> None:
        """Substitui integralmente os insumos da ficha técnica (upsert)."""
        if not items:
            raise ValueError("Uma ficha técnica deve conter ao menos um insumo.")
        self.items = items
