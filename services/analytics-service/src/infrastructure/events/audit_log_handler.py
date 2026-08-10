"""Handler que audita TODO evento de domínio publicado no exchange compartilhado.

Assina o binding curinga `#` (AMQP topic wildcard — "qualquer routing key"),
tornando o `analytics-service` um consumidor passivo e desacoplado da Saga:
nenhum outro serviço precisa saber que a auditoria existe (ADR-001).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from restaurant_database import DatabaseManager
from restaurant_events import DomainEvent
from src.application.use_cases.record_audit_log import RecordAuditLogUseCase
from src.infrastructure.repositories.sqlalchemy_audit_log_repository import (
    SQLAlchemyAuditLogRepository,
)

logger = logging.getLogger(__name__)

AUDIT_ALL_EVENTS_ROUTING_KEY = "#"


def build_audit_log_handler(
    db_manager: DatabaseManager,
) -> Callable[[DomainEvent], Awaitable[None]]:
    """Fábrica do handler curinga de auditoria, ligada à infraestrutura do serviço."""

    async def handle_any_domain_event(event: DomainEvent) -> None:
        async with db_manager.session() as session:
            repository = SQLAlchemyAuditLogRepository(session, event.tenant_id)
            use_case = RecordAuditLogUseCase(audit_log_repository=repository)
            await use_case.execute(
                tenant_id=event.tenant_id,
                event_id=event.event_id,
                event_type=event.event_type,
                payload=event.payload,
                occurred_at=event.occurred_at,
            )
        logger.info("Evento '%s' (%s) auditado.", event.event_type, event.event_id)

    return handle_any_domain_event
