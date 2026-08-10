"""Ponto de Entrada Principal do Microsserviço de Notificações.

Cadastra templates reutilizáveis e enfileira notificações para envio
assíncrono, publicando `notification.requested` (Saga por coreografia,
ADR-001) — o worker `notification_actor` (Dramatiq) consome o evento e
"envia" a mensagem (log estruturado substitui a integração real nesta fase).
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
from src.infrastructure.events.order_status_changed_handler import (
    build_order_status_changed_handler,
)
from src.presentation.api.v1.dependencies import db_manager, event_bus
from src.presentation.api.v1.notification_router import router as notification_router

logger = logging.getLogger(__name__)

ORDER_STATUS_CHANGED_ROUTING_KEY = "order.status_changed"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await event_bus.connect()
        handler = build_order_status_changed_handler(db_manager, event_bus)
        await event_bus.subscribe(
            ORDER_STATUS_CHANGED_ROUTING_KEY,
            handler,
            queue_name="notification-service.order.status_changed",
        )
    except Exception:  # deliberado: log e segue (RabbitMQ pode ainda estar subindo)
        logger.warning("Falha ao conectar/assinar eventos no RabbitMQ no startup.", exc_info=True)
    yield
    await event_bus.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de Notificações — templates e enfileiramento assíncrono.",
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

app.include_router(notification_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
