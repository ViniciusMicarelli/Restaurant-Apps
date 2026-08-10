"""Entidades do Domínio do KDS (Kitchen Display System) — docs/modules/module_breakdown.md §6."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class KDSItemStatus(StrEnum):
    """Máquina de Estados Válida de um item na esteira da cozinha."""

    PENDING = "PENDING"  # Recebido da Saga (order.created), aguardando início do preparo
    PREPARING = "PREPARING"  # Em preparo na estação (US-04.3)
    READY = "READY"  # Pronto para servir/entregar (US-04.3)
    DELIVERED = "DELIVERED"  # Entregue ao garçom/cliente, sai da esteira ativa


class KDSStation(StrEnum):
    """Estação de trabalho da cozinha (docs/modules/module_breakdown.md §6: `KDSStation`).

    O `menu-service` ainda não associa produtos a uma estação específica
    (não há esse atributo no cadastro de produto), então todo item recém
    criado a partir de `order.created` é roteado para `COZINHA_QUENTE` por
    padrão — a estação pode ser realocada manualmente na tela do KDS. Quando
    o cadastro de produto ganhar esse atributo, a atribuição automática por
    estação passa a ser feita aqui, sem qualquer mudança de contrato externo.
    """

    COZINHA_QUENTE = "COZINHA_QUENTE"
    BAR = "BAR"
    SOBREMESAS = "SOBREMESAS"
    OUTROS = "OUTROS"


_VALID_TRANSITIONS: dict[KDSItemStatus, tuple[KDSItemStatus, ...]] = {
    KDSItemStatus.PENDING: (KDSItemStatus.PREPARING,),
    KDSItemStatus.PREPARING: (KDSItemStatus.READY,),
    KDSItemStatus.READY: (KDSItemStatus.DELIVERED,),
    KDSItemStatus.DELIVERED: (),
}


@dataclass
class KDSItem:
    """Item individual na esteira de preparo do KDS (um por item de pedido).

    Attributes:
        id: UUIDv7 do item KDS.
        tenant_id: ID do restaurante proprietário.
        order_id: ID do pedido de origem (`order-service`).
        product_id: ID do produto (`menu-service`).
        product_name: Nome histórico do produto no momento do pedido.
        quantity: Quantidade solicitada.
        station: Estação de preparo responsável.
        table_number: Número da mesa (se aplicável).
        notes: Observações do cliente (ex: 'Sem cebola').
        status: Estado atual na esteira.
        created_at: Quando o item entrou na esteira (usado para o cronômetro
            "há quanto tempo" em tempo real no admin-web).
        ready_at: Quando o item ficou pronto pela primeira vez — junto com
            `created_at`, é a base do SLA de cozinha no dashboard do dono
            (`created_at` → `ready_at` = tempo de preparo). `None` enquanto
            ainda não chegou em `READY`.
        delivered_at: Quando o item foi entregue ao garçom/cliente. `None`
            até chegar em `DELIVERED`.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    quantity: int = 1
    station: KDSStation = KDSStation.COZINHA_QUENTE
    table_number: int | None = None
    notes: str | None = None
    status: KDSItemStatus = KDSItemStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ready_at: datetime | None = None
    delivered_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("A quantidade de um item do KDS deve ser ao menos 1.")

    def transition_to(self, new_status: KDSItemStatus) -> None:
        """Aplica transição válida de máquina de estados, registrando
        `ready_at`/`delivered_at` quando for o caso (base do SLA de cozinha).

        Raises:
            ValueError: Se tentar realizar uma transição de estado proibida.
        """
        if new_status not in _VALID_TRANSITIONS.get(self.status, ()):
            raise ValueError(
                f"Transição inválida de estado: Não é permitido alterar de "
                f"'{self.status.value}' para '{new_status.value}'."
            )
        self.status = new_status
        if new_status == KDSItemStatus.READY:
            self.ready_at = datetime.now(UTC)
        elif new_status == KDSItemStatus.DELIVERED:
            self.delivered_at = datetime.now(UTC)
