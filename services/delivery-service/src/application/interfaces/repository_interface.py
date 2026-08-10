"""Contratos de repositório e integrações do serviço de Delivery."""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.entities.delivery import Delivery


class DeliveryRepositoryInterface(Protocol):
    async def get_by_id(self, delivery_id: uuid.UUID) -> Delivery | None: ...

    async def list_all(self) -> list[Delivery]: ...

    async def add(self, delivery: Delivery) -> Delivery: ...

    async def save(self, delivery: Delivery) -> Delivery: ...


class ExternalDeliveryProviderInterface(Protocol):
    """Ponto de extensão para integração real com plataformas terceiras
    (iFood, Rappi — docs/modules/module_breakdown.md §9).

    Nenhuma implementação real é fornecida nesta fase (Tier B): a interface
    existe para permitir plugar um cliente HTTP real (`IFoodDeliveryProvider`,
    `RappiDeliveryProvider`, etc.) sem alterar os casos de uso que a consomem.
    """

    async def request_external_courier(self, delivery: Delivery) -> str:
        """Solicita um entregador à plataforma terceira e retorna seu identificador externo."""
        ...
