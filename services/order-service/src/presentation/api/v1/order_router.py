"""Rotas FastAPI de Pedidos — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from restaurant_events import EventBus
from restaurant_security.rbac import (
    KITCHEN_STAFF,
    MANAGER,
    RESTAURANT_OWNER,
    WAITER,
    CurrentUser,
    require_role,
    require_tenant_id,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.order_dtos import (
    CancelOrderRequest,
    CreateOrderRequest,
    OrderResponse,
    TransitionOrderStatusRequest,
)
from src.application.interfaces.repository_interface import IdempotencyStoreInterface
from src.application.use_cases.cancel_order import CancelOrderUseCase
from src.application.use_cases.create_order import CreateOrderUseCase
from src.application.use_cases.get_order import GetOrderUseCase, ListOrdersUseCase
from src.application.use_cases.transition_order_status import TransitionOrderStatusUseCase
from src.config import settings
from src.presentation.api.v1.dependencies import (
    get_current_user,
    get_db_session,
    get_event_bus,
    get_idempotency_store,
    order_repository_for,
)

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo pedido",
)
async def create_order(  # noqa: PLR0913, PLR0917 - dependências injetadas via FastAPI, não parâmetros de negócio
    payload: CreateOrderRequest,
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    idempotency_store: Annotated[IdempotencyStoreInterface, Depends(get_idempotency_store)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> OrderResponse:
    use_case = CreateOrderUseCase(
        order_repository=order_repository_for(session, tenant_id),
        idempotency_store=idempotency_store,
        event_bus=event_bus,
    )
    response = await use_case.execute(
        tenant_id=tenant_id,
        order_type=payload.order_type,
        items=payload.items,
        table_number=payload.table_number,
        command_id=payload.command_id,
        idempotency_key=idempotency_key,
    )
    await session.commit()
    return response


@router.get("", response_model=list[OrderResponse], summary="Lista pedidos do tenant")
async def list_orders(
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    table_number: Annotated[int | None, Query(ge=1)] = None,
    command_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[OrderResponse]:
    use_case = ListOrdersUseCase(order_repository=order_repository_for(session, tenant_id))
    return await use_case.execute(table_number=table_number, command_id=command_id)


@router.get("/{order_id}", response_model=OrderResponse, summary="Consulta um pedido")
async def get_order(
    order_id: uuid.UUID,
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrderResponse:
    use_case = GetOrderUseCase(order_repository=order_repository_for(session, tenant_id))
    return await use_case.execute(order_id=order_id)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Atualiza o status do pedido (Garçom/Cozinha/Manager/Owner)",
)
async def transition_order_status(
    order_id: uuid.UUID,
    payload: TransitionOrderStatusRequest,
    current_user: Annotated[
        CurrentUser,
        Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER, WAITER, KITCHEN_STAFF)),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
) -> OrderResponse:
    use_case = TransitionOrderStatusUseCase(
        order_repository=order_repository_for(session, current_user.tenant_id),
        event_bus=event_bus,
    )
    response = await use_case.execute(order_id=order_id, new_status=payload.new_status)
    await session.commit()
    return response


@router.post(
    "/{order_id}/cancel", response_model=OrderResponse, summary="Cancela um pedido (Manager/Owner)"
)
async def cancel_order(
    order_id: uuid.UUID,
    payload: CancelOrderRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrderResponse:
    use_case = CancelOrderUseCase(
        order_repository=order_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        order_id=order_id, cancellation_reason=payload.cancellation_reason
    )
    await session.commit()
    return response


@router.get("/health/check", summary="Health Check do Serviço de Pedidos")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
