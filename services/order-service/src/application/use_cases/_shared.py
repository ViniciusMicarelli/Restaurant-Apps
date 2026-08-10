"""Helper interno: monta o DTO de resposta de um `Order`."""

from __future__ import annotations

from src.application.dtos.order_dtos import OrderItemResponse, OrderResponse
from src.domain.entities.order import Order


def to_order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        tenant_id=order.tenant_id,
        order_type=order.order_type,
        table_number=order.table_number,
        command_id=order.command_id,
        status=order.status,
        items=[
            OrderItemResponse(
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                notes=item.notes,
                total_price=item.total_price,
            )
            for item in order.items
        ],
        total_amount=order.total_amount,
        cancellation_reason=order.cancellation_reason,
        created_at=order.created_at,
    )
