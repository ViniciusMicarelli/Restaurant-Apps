"""Implementação concreta de `OrderRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.order import Order, OrderItem
from src.infrastructure.models.order_model import OrderModel


def _to_entity(model: OrderModel) -> Order:
    return Order(
        id=model.id,
        tenant_id=model.tenant_id,
        order_type=model.order_type,
        table_number=model.table_number,
        command_id=model.command_id,
        status=model.status,
        items=[
            OrderItem(
                product_id=uuid.UUID(item["product_id"]),
                product_name=item["product_name"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
                notes=item.get("notes"),
            )
            for item in model.items
        ],
        cancellation_reason=model.cancellation_reason,
        created_at=model.created_at,
    )


def _items_to_json(order: Order) -> list[dict[str, object]]:
    return [
        {
            "product_id": str(item.product_id),
            "product_name": item.product_name,
            "unit_price": item.unit_price,
            "quantity": item.quantity,
            "notes": item.notes,
        }
        for item in order.items
    ]


class SQLAlchemyOrderRepository(SQLAlchemyRepository[OrderModel]):
    model = OrderModel

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        model = await super().get_model_by_id(order_id)
        return _to_entity(model) if model is not None else None

    async def list_all(
        self, *, table_number: int | None = None, command_id: uuid.UUID | None = None
    ) -> list[Order]:
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == self._tenant_id, self.model.deleted_at.is_(None))
            .order_by(self.model.created_at.asc())
            .limit(1000)
        )
        if table_number is not None:
            stmt = stmt.where(self.model.table_number == table_number)
        if command_id is not None:
            stmt = stmt.where(self.model.command_id == command_id)
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def add(self, order: Order) -> Order:
        model = OrderModel(
            id=order.id,
            tenant_id=order.tenant_id,
            order_type=order.order_type,
            table_number=order.table_number,
            command_id=order.command_id,
            status=order.status,
            items=_items_to_json(order),
            cancellation_reason=order.cancellation_reason,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, order: Order) -> Order:
        model = await self._session.get(OrderModel, order.id)
        if model is None:
            msg = f"Pedido '{order.id}' não encontrado para atualização."
            raise LookupError(msg)
        model.status = order.status
        model.cancellation_reason = order.cancellation_reason
        model.items = _items_to_json(order)
        saved = await super().save_model(model)
        return _to_entity(saved)
