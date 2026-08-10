"""Entidade `Coupon` — cupom de desconto (docs/modules/module_breakdown.md §10)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class DiscountType(StrEnum):
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"


_MAX_PERCENTAGE = 100


@dataclass
class Coupon:
    """Cupom de desconto validável por código, com janela de validade e limite de usos.

    Attributes:
        id: UUIDv7 do cupom.
        tenant_id: ID do restaurante proprietário.
        code: Código único do cupom (normalizado em maiúsculas).
        discount_type: `PERCENTAGE` (% sobre o total) ou `FIXED` (valor fixo em R$).
        discount_value: Percentual (0-100) ou valor fixo, conforme `discount_type`.
        valid_from: Início da janela de validade.
        valid_until: Fim da janela de validade.
        max_uses: Limite total de usos (`None` = ilimitado).
        times_used: Quantidade de vezes já aplicado.
        active: Permite desativar o cupom manualmente antes do fim da validade.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    code: str
    discount_type: DiscountType
    discount_value: float
    valid_from: datetime
    valid_until: datetime
    max_uses: int | None = None
    times_used: int = 0
    active: bool = True

    def __post_init__(self) -> None:
        self.code = self.code.strip().upper()
        # SQLite (usado em testes de integração) não preserva o offset de fuso
        # horário em colunas `DateTime(timezone=True)` — datas lidas de volta
        # do banco chegam "naive". Normalizamos para UTC aqui, na fronteira do
        # domínio, para que comparações em `is_valid_at` nunca dependam do
        # dialeto de banco usado (Postgres real preserva tz; SQLite não).
        if self.valid_from.tzinfo is None:
            self.valid_from = self.valid_from.replace(tzinfo=UTC)
        if self.valid_until.tzinfo is None:
            self.valid_until = self.valid_until.replace(tzinfo=UTC)
        if not self.code:
            raise ValueError("O código do cupom não pode ser vazio.")
        if self.discount_value <= 0:
            raise ValueError("O valor do desconto deve ser positivo.")
        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value > _MAX_PERCENTAGE:
            raise ValueError("O desconto percentual não pode ultrapassar 100%.")
        if self.valid_until <= self.valid_from:
            raise ValueError("A data final de validade deve ser posterior à data inicial.")
        if self.max_uses is not None and self.max_uses < 1:
            raise ValueError("O limite de usos, se informado, deve ser ao menos 1.")

    def is_valid_at(self, moment: datetime) -> bool:
        """Verifica se o cupom pode ser aplicado no instante informado."""
        if not self.active:
            return False
        if not (self.valid_from <= moment <= self.valid_until):
            return False
        return not (self.max_uses is not None and self.times_used >= self.max_uses)

    def calculate_discount(self, order_total: float) -> float:
        """Calcula o valor de desconto para um total de pedido, sem exceder o próprio total."""
        if order_total <= 0:
            raise ValueError("O total do pedido deve ser positivo para aplicar um cupom.")

        if self.discount_type == DiscountType.PERCENTAGE:
            discount = order_total * (self.discount_value / 100)
        else:
            discount = self.discount_value

        return round(min(discount, order_total), 2)

    def register_use(self) -> None:
        """Incrementa o contador de usos — chamado após a validação de `is_valid_at`."""
        self.times_used += 1
