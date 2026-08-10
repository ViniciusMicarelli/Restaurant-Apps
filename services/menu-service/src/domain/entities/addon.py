"""Entidades de Domínio: Grupos de Adicionais (Add-ons) de um Produto."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class AddonOption:
    """Uma opção selecionável dentro de um grupo de adicionais (ex: 'Bacon extra')."""

    name: str
    price_delta: float = 0.0


@dataclass
class AddonGroup:
    """Grupo de adicionais de um produto (ex: 'Escolha o ponto da carne').

    Attributes:
        min_selections: Mínimo de opções que o cliente deve escolher (0 = opcional).
        max_selections: Máximo de opções que o cliente pode escolher.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    name: str
    min_selections: int = 0
    max_selections: int = 1
    options: list[AddonOption] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.min_selections < 0:
            raise ValueError("min_selections não pode ser negativo.")
        if self.max_selections < self.min_selections:
            raise ValueError("max_selections não pode ser menor que min_selections.")
