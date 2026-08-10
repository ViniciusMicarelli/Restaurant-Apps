"""Entidade de Domínio: Produto do Cardápio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class Product:
    """Item vendável do cardápio.

    Attributes:
        price: Preço de venda ao cliente.
        cost_price: Custo de produção (usado em relatórios de margem — analytics-service).
        tax_rate: Alíquota de imposto aplicada (percentual).
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    category_id: uuid.UUID
    name: str
    description: str = ""
    price: float = 0.0
    cost_price: float = 0.0
    tax_rate: float = 0.0
    photo_url: str = ""
    display_order: int = 0
    is_active: bool = True

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError("O preço do produto não pode ser negativo.")
        if self.cost_price < 0:
            raise ValueError("O custo do produto não pode ser negativo.")

    @property
    def margin(self) -> float:
        """Margem bruta (preço - custo). Usado por relatórios de análise de cardápio."""
        return round(self.price - self.cost_price, 2)
