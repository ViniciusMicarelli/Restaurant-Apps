"""Rotas FastAPI de Analytics & Auditoria — camada fina: valida DTO, chama o
UseCase, devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md).

Somente leitura: `AuditLog` só nasce a partir de eventos de domínio
consumidos (`src/infrastructure/events/audit_log_handler.py`), nunca via
requisição HTTP direta — não existe endpoint de escrita aqui.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from restaurant_common.pagination import PaginatedResponse
from restaurant_security.rbac import MANAGER, RESTAURANT_OWNER, CurrentUser, require_role
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.audit_log_dtos import AuditLogResponse
from src.application.use_cases.list_audit_logs import ListAuditLogsUseCase
from src.config import settings
from src.presentation.api.v1.dependencies import (
    audit_log_repository_for,
    get_current_user,
    get_db_session,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Audit"])

_AUDIT_ROLES = (RESTAURANT_OWNER, MANAGER)


@router.get(
    "/audit-logs",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Consulta paginada do log de auditoria (todos os eventos de domínio)",
)
async def list_audit_logs(
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_AUDIT_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    event_type: Annotated[str | None, Query()] = None,
) -> PaginatedResponse[AuditLogResponse]:
    use_case = ListAuditLogsUseCase(
        audit_log_repository=audit_log_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(limit=limit, offset=offset, event_type=event_type)


@router.get("/health/check", summary="Health Check do Serviço de Analytics & Auditoria")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
