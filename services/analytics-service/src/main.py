"""Ponto de Entrada Principal do Microsserviço de Analytics & Auditoria.

Escopo Tier B (base sólida): consome TODO evento de domínio publicado no
exchange compartilhado (binding curinga `#`) e persiste um `AuditLog`
imutável — relatórios gerenciais (vendas por hora/dia, curva ABC, DRE
simplificado) ficam para uma fase futura, conforme
docs/modules/module_breakdown.md §12.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from restaurant_common.problem_details import register_exception_handlers
from restaurant_security.tenant_context import TenantContextMiddleware
from src.config import settings
from src.infrastructure.events.audit_log_handler import (
    AUDIT_ALL_EVENTS_ROUTING_KEY,
    build_audit_log_handler,
)
from src.presentation.api.v1.analytics_router import router as analytics_router
from src.presentation.api.v1.dependencies import db_manager, event_bus

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await event_bus.connect()
        handler = build_audit_log_handler(db_manager)
        await event_bus.subscribe(
            AUDIT_ALL_EVENTS_ROUTING_KEY, handler, queue_name="analytics-service.audit"
        )
    except Exception:  # deliberado: log e segue (RabbitMQ pode ainda estar subindo)
        logger.warning("Falha ao conectar/assinar eventos no RabbitMQ no startup.", exc_info=True)
    yield
    await event_bus.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de Analytics & Auditoria — consulta paginada do log de auditoria imutável.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    TenantContextMiddleware, jwt_secret_key=settings.jwt_secret_key.get_secret_value()
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
