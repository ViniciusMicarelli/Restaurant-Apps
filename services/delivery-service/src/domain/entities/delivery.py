"""Entidade `Delivery` — entrega/retirada de um pedido (docs/modules/module_breakdown.md §9).

Escopo Tier B (base sólida): rastreia o ciclo de vida de uma entrega própria
e expõe o ponto de extensão (`ExternalDeliveryProviderInterface`) para
integrações reais com iFood/Rappi no futuro, sem implementá-las agora.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum


class DeliveryStatus(StrEnum):
    """Máquina de Estados Válida da entrega."""

    PENDING = "PENDING"  # Aguardando atribuição de entregador
    ASSIGNED = "ASSIGNED"  # Entregador atribuído
    IN_TRANSIT = "IN_TRANSIT"  # A caminho do cliente
    DELIVERED = "DELIVERED"  # Entregue
    CANCELLED = "CANCELLED"  # Cancelada


_VALID_TRANSITIONS: dict[DeliveryStatus, tuple[DeliveryStatus, ...]] = {
    DeliveryStatus.PENDING: (DeliveryStatus.ASSIGNED, DeliveryStatus.CANCELLED),
    DeliveryStatus.ASSIGNED: (DeliveryStatus.IN_TRANSIT, DeliveryStatus.CANCELLED),
    DeliveryStatus.IN_TRANSIT: (DeliveryStatus.DELIVERED, DeliveryStatus.CANCELLED),
    DeliveryStatus.DELIVERED: (),
    DeliveryStatus.CANCELLED: (),
}


@dataclass
class Delivery:
    """Entrega de um pedido até o endereço do cliente (Aggregate Root).

    Attributes:
        id: UUIDv7 da entrega.
        tenant_id: ID do restaurante proprietário.
        order_id: ID do pedido de origem (`order-service`).
        delivery_address: Endereço completo de entrega.
        courier_name: Nome do entregador atribuído (nulo até `ASSIGNED`).
        status: Estado atual na máquina de estados.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    delivery_address: str
    courier_name: str | None = None
    status: DeliveryStatus = DeliveryStatus.PENDING

    def __post_init__(self) -> None:
        if not self.delivery_address.strip():
            raise ValueError("O endereço de entrega não pode ser vazio.")

    def assign_courier(self, courier_name: str) -> None:
        if not courier_name.strip():
            raise ValueError("O nome do entregador não pode ser vazio.")
        self.transition_to(DeliveryStatus.ASSIGNED)
        self.courier_name = courier_name

    def transition_to(self, new_status: DeliveryStatus) -> None:
        """Aplica transição válida de máquina de estados.

        Raises:
            ValueError: Se tentar realizar uma transição de estado proibida.
        """
        if new_status not in _VALID_TRANSITIONS.get(self.status, ()):
            raise ValueError(
                f"Transição inválida de estado: Não é permitido alterar de "
                f"'{self.status.value}' para '{new_status.value}'."
            )
        self.status = new_status
