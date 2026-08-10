"""Rotas FastAPI de Delivery — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from restaurant_security.rbac import (
    MANAGER,
    RESTAURANT_OWNER,
    WAITER,
    CurrentUser,
    require_role,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.delivery_dtos import (
    AssignCourierRequest,
    CreateDeliveryRequest,
    DeliveryResponse,
    UpdateDeliveryStatusRequest,
)
from src.application.use_cases.create_delivery import CreateDeliveryUseCase, ListDeliveriesUseCase
from src.application.use_cases.update_delivery_status import (
    AssignCourierUseCase,
    UpdateDeliveryStatusUseCase,
)
from src.config import settings
from src.presentation.api.v1.dependencies import (
    delivery_repository_for,
    get_current_user,
    get_db_session,
)

router = APIRouter(prefix="/api/v1/deliveries", tags=["Delivery"])

_DELIVERY_ROLES = (RESTAURANT_OWNER, MANAGER, WAITER)


@router.post(
    "",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma entrega a partir de um pedido de delivery",
)
async def create_delivery(
    payload: CreateDeliveryRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_DELIVERY_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DeliveryResponse:
    use_case = CreateDeliveryUseCase(
        delivery_repository=delivery_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        order_id=payload.order_id,
        delivery_address=payload.delivery_address,
    )
    await session.commit()
    return response


@router.get("", response_model=list[DeliveryResponse], summary="Lista as entregas do tenant")
async def list_deliveries(
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_DELIVERY_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[DeliveryResponse]:
    use_case = ListDeliveriesUseCase(
        delivery_repository=delivery_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute()


@router.post(
    "/{delivery_id}/assign-courier",
    response_model=DeliveryResponse,
    summary="Atribui um entregador próprio à entrega",
)
async def assign_courier(
    delivery_id: uuid.UUID,
    payload: AssignCourierRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_DELIVERY_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DeliveryResponse:
    use_case = AssignCourierUseCase(
        delivery_repository=delivery_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(delivery_id=delivery_id, courier_name=payload.courier_name)
    await session.commit()
    return response


@router.patch(
    "/{delivery_id}/status", response_model=DeliveryResponse, summary="Atualiza o status da entrega"
)
async def update_delivery_status(
    delivery_id: uuid.UUID,
    payload: UpdateDeliveryStatusRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_DELIVERY_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DeliveryResponse:
    use_case = UpdateDeliveryStatusUseCase(
        delivery_repository=delivery_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(delivery_id=delivery_id, new_status=payload.new_status)
    await session.commit()
    return response


@router.get("/health/check", summary="Health Check do Serviço de Delivery")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
