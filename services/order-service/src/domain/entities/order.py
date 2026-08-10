"""Entidades do Domínio do Motor de Pedidos (DDD)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class OrderStatus(StrEnum):
    """Máquina de Estados Válida do Pedido."""

    PENDING = "PENDING"  # Pedido criado, aguardando confirmação ou pagamento
    PREPARING = "PREPARING"  # Confirmado, em preparo na cozinha (KDS)
    READY = "READY"  # Pronto para servir ou entregar
    DELIVERED = "DELIVERED"  # Entregue ao cliente na mesa ou delivery
    CANCELLED = "CANCELLED"  # Cancelado com motivo registrado em auditoria


class OrderType(StrEnum):
    """Origem / Tipo de Pedido."""

    TABLE = "TABLE"  # Atendimento presencial na mesa do salão
    COUNTER = "COUNTER"  # Balcão / Retirada rápida (Takeout)
    QR_CODE = "QR_CODE"  # Autoatendimento via QR Code do cliente
    DELIVERY = "DELIVERY"  # Delivery (iFood / Próprio)


_VALID_TRANSITIONS: dict[OrderStatus, tuple[OrderStatus, ...]] = {
    OrderStatus.PENDING: (OrderStatus.PREPARING, OrderStatus.CANCELLED),
    OrderStatus.PREPARING: (OrderStatus.READY, OrderStatus.CANCELLED),
    OrderStatus.READY: (OrderStatus.DELIVERED, OrderStatus.CANCELLED),
    OrderStatus.DELIVERED: (),
    OrderStatus.CANCELLED: (),
}


@dataclass
class OrderItem:
    """Item individual pertencente a um pedido.

    Attributes:
        product_id: ID do produto (menu-service).
        product_name: Nome histórico do produto no momento da venda.
        unit_price: Preço unitário no momento da venda.
        quantity: Quantidade de unidades.
        notes: Observações do cliente (ex: 'Sem cebola').
    """

    product_id: uuid.UUID
    product_name: str
    unit_price: float
    quantity: int = 1
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("A quantidade de um item deve ser ao menos 1.")
        if self.unit_price < 0:
            raise ValueError("O preço unitário não pode ser negativo.")

    @property
    def total_price(self) -> float:
        return round(self.unit_price * self.quantity, 2)


@dataclass
class Order:
    """Entidade Raiz do Agregado de Pedido (Aggregate Root).

    Attributes:
        id: UUIDv7 do pedido.
        tenant_id: ID do restaurante proprietário.
        table_number: Número da mesa (se aplicável).
        order_type: Origem do pedido.
        status: Estado atual na máquina de estados.
        items: Itens incluídos no pedido.
        cancellation_reason: Motivo em caso de cancelamento.
        command_id: Comanda (dining-service) à qual este pedido pertence, se
            aberta numa mesa — permite somar o total da comanda e aplicar a
            taxa de serviço no fechamento (docs/modules/module_breakdown.md §5/§8).
            `None` para pedidos sem comanda (ex: balcão, delivery).
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_type: OrderType
    table_number: int | None = None
    status: OrderStatus = OrderStatus.PENDING
    items: list[OrderItem] = field(default_factory=list)
    cancellation_reason: str | None = None
    command_id: uuid.UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError("Um pedido deve conter ao menos um item.")

    @property
    def total_amount(self) -> float:
        """Calcula o valor total acumulado dos itens do pedido."""
        return round(sum(item.total_price for item in self.items), 2)

    def transition_to(self, new_status: OrderStatus) -> None:
        """Aplica transição válida de máquina de estados.

        Raises:
            ValueError: Se tentar realizar uma transição de estado proibida.
        """
        if new_status not in _VALID_TRANSITIONS.get(self.status, ()):
            raise ValueError(
                f"Transição inválida de estado: Não é permitido alterar de '{self.status.value}' para '{new_status.value}'."
            )
        self.status = new_status

    def cancel(self, reason: str) -> None:
        """Cancela o pedido, exigindo um motivo registrável em auditoria."""
        if not reason.strip():
            raise ValueError("O cancelamento de um pedido exige um motivo.")
        self.transition_to(OrderStatus.CANCELLED)
        self.cancellation_reason = reason
