"""Helpers compartilhados entre casos de uso do serviço de Cozinha/KDS."""

from __future__ import annotations

from src.application.dtos.kds_dtos import KDSItemResponse
from src.domain.entities.kds_item import KDSItem


def to_kds_item_response(item: KDSItem) -> KDSItemResponse:
    return KDSItemResponse(
        id=item.id,
        tenant_id=item.tenant_id,
        order_id=item.order_id,
        product_id=item.product_id,
        product_name=item.product_name,
        quantity=item.quantity,
        station=item.station,
        table_number=item.table_number,
        notes=item.notes,
        status=item.status,
        created_at=item.created_at,
        ready_at=item.ready_at,
        delivered_at=item.delivered_at,
    )
