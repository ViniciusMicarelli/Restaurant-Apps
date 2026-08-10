"""Ponto de Entrada Principal do Microsserviço de Cozinha e KDS (Kitchen Display System).

Gerencia a esteira de itens em preparo por estação (Cozinha Quente, Bar,
Sobremesas) e fornece conexões WebSocket em tempo real para os monitores da
cozinha e apps dos garçons. Consome o evento `order.created` (Saga por
coreografia, ADR-001) para popular a esteira automaticamente.
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
from src.infrastructure.events.order_created_handler import build_order_created_handler
from src.presentation.api.v1.dependencies import connection_manager, db_manager, event_bus
from src.presentation.api.v1.kitchen_router import router as kitchen_router

logger = logging.getLogger(__name__)

ORDER_CREATED_ROUTING_KEY = "order.created"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await event_bus.connect()
        handler = build_order_created_handler(db_manager, connection_manager)
        # `queue_name` explícito: `order.created` também é consumido pelo
        # `inventory-service` — sem um nome de fila exclusivo por serviço, os
        # dois concorreriam pela mesma fila e só um receberia cada evento.
        await event_bus.subscribe(
            ORDER_CREATED_ROUTING_KEY, handler, queue_name="kitchen-service.order.created"
        )
    except Exception:  # deliberado: log e segue (RabbitMQ pode ainda estar subindo)
        logger.warning("Falha ao conectar/assinar eventos no RabbitMQ no startup.", exc_info=True)
    yield
    await event_bus.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API do KDS (Kitchen Display System) e Transmissão em Tempo Real via WebSockets.",
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

app.include_router(kitchen_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
