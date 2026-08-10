"""Implementação stub de `ExternalDeliveryProviderInterface` — Tier B (sem integração real).

Documenta o ponto de extensão sem fingir uma integração que não existe:
qualquer tentativa de uso levanta `NotImplementedError` explicitamente, em
vez de simular uma resposta de sucesso falsa.
"""

from __future__ import annotations

from src.domain.entities.delivery import Delivery


class NotImplementedExternalDeliveryProvider:
    """Usado como o `ExternalDeliveryProviderInterface` padrão até uma
    integração real (iFood/Rappi) ser implementada e configurada via `.env`.
    """

    async def request_external_courier(self, delivery: Delivery) -> str:
        raise NotImplementedError(
            "Integração com plataforma de entrega externa ainda não configurada "
            f"para o pedido '{delivery.order_id}'. Configure um provedor real "
            "(iFood/Rappi) via variável de ambiente antes de usar entrega externa."
        )
