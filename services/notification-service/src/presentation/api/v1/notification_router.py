"""Rotas FastAPI de Notificações — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from restaurant_events import EventBus
from restaurant_security.rbac import (
    CASHIER,
    KITCHEN_STAFF,
    MANAGER,
    RESTAURANT_OWNER,
    WAITER,
    CurrentUser,
    require_role,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.notification_dtos import (
    CreateNotificationTemplateRequest,
    NotificationResponse,
    NotificationTemplateResponse,
    QueueNotificationRequest,
)
from src.application.use_cases.create_notification_template import (
    CreateNotificationTemplateUseCase,
)
from src.application.use_cases.queue_notification import (
    ListNotificationsUseCase,
    QueueNotificationUseCase,
)
from src.config import settings
from src.presentation.api.v1.dependencies import (
    get_current_user,
    get_db_session,
    get_event_bus,
    notification_repository_for,
    template_repository_for,
)

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

_MANAGE_TEMPLATE_ROLES = (RESTAURANT_OWNER, MANAGER)
_QUEUE_NOTIFICATION_ROLES = (RESTAURANT_OWNER, MANAGER, CASHIER, WAITER, KITCHEN_STAFF)


@router.post(
    "/templates",
    response_model=NotificationTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um template reutilizável de notificação",
)
async def create_template(
    payload: CreateNotificationTemplateRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_MANAGE_TEMPLATE_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationTemplateResponse:
    use_case = CreateNotificationTemplateUseCase(
        template_repository=template_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        code=payload.code,
        channel=payload.channel,
        body=payload.body,
        subject=payload.subject,
    )
    await session.commit()
    return response


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enfileira uma notificação para envio assíncrono",
)
async def queue_notification(
    payload: QueueNotificationRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_QUEUE_NOTIFICATION_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
) -> NotificationResponse:
    use_case = QueueNotificationUseCase(
        notification_repository=notification_repository_for(session, current_user.tenant_id),
        template_repository=template_repository_for(session, current_user.tenant_id),
        event_bus=event_bus,
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        channel=payload.channel,
        recipient=payload.recipient,
        template_code=payload.template_code,
        context=payload.context,
    )
    await session.commit()
    return response


@router.get(
    "", response_model=list[NotificationResponse], summary="Lista as notificações do tenant"
)
async def list_notifications(
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_QUEUE_NOTIFICATION_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[NotificationResponse]:
    use_case = ListNotificationsUseCase(
        notification_repository=notification_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute()


@router.get("/health/check", summary="Health Check do Serviço de Notificações")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
