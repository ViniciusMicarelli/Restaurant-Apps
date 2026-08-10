"""Rotas FastAPI de Cozinha/KDS — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

import jwt as pyjwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from restaurant_security.jwt import decode_access_token
from restaurant_security.rbac import (
    KITCHEN_STAFF,
    MANAGER,
    RESTAURANT_OWNER,
    CurrentUser,
    require_role,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.kds_dtos import KDSItemResponse, UpdateKDSItemStatusRequest
from src.application.interfaces.repository_interface import KDSBroadcasterInterface
from src.application.use_cases.list_kds_items import ListKDSItemsUseCase
from src.application.use_cases.update_kds_item_status import UpdateKDSItemStatusUseCase
from src.config import settings
from src.domain.entities.kds_item import KDSStation
from src.presentation.api.v1.dependencies import (
    connection_manager,
    get_broadcaster,
    get_current_user,
    get_db_session,
    kds_item_repository_for,
    kds_log_repository_for,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Kitchen & KDS"])

_KDS_ROLES = (RESTAURANT_OWNER, MANAGER, KITCHEN_STAFF)


@router.get(
    "/api/v1/kitchen/kds/items",
    response_model=list[KDSItemResponse],
    summary="Lista os itens ativos na esteira do KDS",
)
async def list_kds_items(
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_KDS_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    station: Annotated[KDSStation | None, Query()] = None,
) -> list[KDSItemResponse]:
    use_case = ListKDSItemsUseCase(
        kds_item_repository=kds_item_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(station=station)


@router.patch(
    "/api/v1/kitchen/kds/items/{kds_item_id}/status",
    response_model=KDSItemResponse,
    summary="Atualiza o status de um item do KDS (Cozinha/Manager/Owner)",
)
async def update_kds_item_status(
    kds_item_id: uuid.UUID,
    payload: UpdateKDSItemStatusRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_KDS_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    broadcaster: Annotated[KDSBroadcasterInterface, Depends(get_broadcaster)],
) -> KDSItemResponse:
    use_case = UpdateKDSItemStatusUseCase(
        kds_item_repository=kds_item_repository_for(session, current_user.tenant_id),
        kds_log_repository=kds_log_repository_for(session, current_user.tenant_id),
        broadcaster=broadcaster,
    )
    response = await use_case.execute(kds_item_id=kds_item_id, new_status=payload.new_status)
    await session.commit()
    return response


@router.websocket("/ws/v1/kitchen/kds")
async def kds_websocket_endpoint(websocket: WebSocket, token: str) -> None:
    """Endpoint de WebSocket em tempo real para telas KDS e apps de garçons.

    Exige um Access Token JWT válido via query string (`?token=...`) — o
    `tenant_id` do token escopa quais broadcasts esta conexão recebe,
    preservando o isolamento de multi-tenancy (ADR-003) também em tempo real.
    """
    try:
        claims = decode_access_token(token, settings.jwt_secret_key.get_secret_value())
        if claims.get("role") not in _KDS_ROLES:
            raise pyjwt.InvalidTokenError("Papel sem permissão para o KDS.")
        tenant_id = uuid.UUID(str(claims["tenant_id"]))
    except Exception:
        logger.warning("Conexão WebSocket do KDS rejeitada: token inválido.", exc_info=True)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(websocket, tenant_id)
    try:
        while True:
            # Mantém a conexão aberta escutando heartbeats (ping/pong) do cliente.
            data = await websocket.receive_text()
            await websocket.send_json({"event": "PONG", "payload": data})
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, tenant_id)


@router.get("/api/v1/kitchen/health/check", summary="Health Check do Serviço de Cozinha/KDS")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
