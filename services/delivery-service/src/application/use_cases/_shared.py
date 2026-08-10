"""Helpers compartilhados entre casos de uso do serviço de Delivery."""

from __future__ import annotations

from src.application.dtos.delivery_dtos import DeliveryResponse
from src.domain.entities.delivery import Delivery


def to_delivery_response(delivery: Delivery) -> DeliveryResponse:
    return DeliveryResponse(
        id=delivery.id,
        tenant_id=delivery.tenant_id,
        order_id=delivery.order_id,
        delivery_address=delivery.delivery_address,
        courier_name=delivery.courier_name,
        status=delivery.status,
    )
