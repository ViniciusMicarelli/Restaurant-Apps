"""Entidade `InventoryItem` — insumo controlado em estoque (docs/modules/module_breakdown.md §7)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum

from src.domain.exceptions import InsufficientStockException


class InventoryUnit(StrEnum):
    """Unidade de medida do insumo."""

    KG = "KG"
    G = "G"
    L = "L"
    ML = "ML"
    UN = "UN"


@dataclass
class InventoryItem:
    """Insumo controlado em estoque, com quantidade atual e mínima (alerta).

    Attributes:
        id: UUIDv7 do insumo.
        tenant_id: ID do restaurante proprietário.
        name: Nome do insumo (ex: 'Pão de Hambúrguer', 'Queijo Cheddar').
        unit: Unidade de medida.
        current_quantity: Quantidade atualmente em estoque.
        minimum_quantity: Limiar mínimo — abaixo disso, `is_below_minimum` alerta.
        supplier_id: Fornecedor associado (opcional).
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    unit: InventoryUnit
    current_quantity: float = 0.0
    minimum_quantity: float = 0.0
    supplier_id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("O nome do insumo não pode ser vazio.")
        if self.current_quantity < 0:
            raise ValueError("A quantidade em estoque não pode ser negativa.")
        if self.minimum_quantity < 0:
            raise ValueError("A quantidade mínima não pode ser negativa.")

    @property
    def is_below_minimum(self) -> bool:
        """Indica se o insumo está abaixo do limiar de alerta de estoque mínimo."""
        return self.current_quantity < self.minimum_quantity

    def increase(self, quantity: float) -> None:
        """Aumenta o estoque (entrada, devolução)."""
        if quantity <= 0:
            raise ValueError("A quantidade de um movimento de entrada deve ser positiva.")
        self.current_quantity = round(self.current_quantity + quantity, 3)

    def decrease(self, quantity: float, *, allow_negative: bool = False) -> None:
        """Reduz o estoque (perda, baixa automática de venda).

        Args:
            quantity: Quantidade positiva a ser deduzida.
            allow_negative: Quando `True` (baixa automática por venda via Saga),
                permite que o estoque fique negativo — a operação de venda já
                ocorreu em outro serviço e não pode ser revertida por aqui
                (consistência eventual); o estoque negativo sinaliza a
                necessidade de reposição urgente. Movimentações manuais
                (perdas registradas por um operador) mantêm `allow_negative=False`.

        Raises:
            InsufficientStockException: Se `allow_negative=False` e a
                dedução resultaria em estoque negativo.
        """
        if quantity <= 0:
            raise ValueError("A quantidade de um movimento de saída deve ser positiva.")

        resulting = round(self.current_quantity - quantity, 3)
        if resulting < 0 and not allow_negative:
            raise InsufficientStockException(self.name, self.current_quantity, quantity)

        self.current_quantity = resulting

    def adjust_to_counted_quantity(self, counted_quantity: float) -> float:
        """Aplica uma contagem de inventário, ajustando para o valor contado.

        Returns:
            O delta aplicado (positivo ou negativo) — usado para registrar o `StockMovement`.
        """
        if counted_quantity < 0:
            raise ValueError("A quantidade contada não pode ser negativa.")

        delta = round(counted_quantity - self.current_quantity, 3)
        self.current_quantity = round(counted_quantity, 3)
        return delta
