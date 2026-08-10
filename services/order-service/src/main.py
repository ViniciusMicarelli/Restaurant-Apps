"""Ponto de Entrada Principal do Microsserviço Motor de Pedidos e Orquestrador de Sagas.

Gerencia o ciclo de vida completo dos pedidos de salão, balcão e delivery,
publicando eventos de domínio para a Saga por coreografia (ADR-001).
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
from src.presentation.api.v1.dependencies import event_bus
from src.presentation.api.v1.order_router import router as order_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await event_bus.connect()
    except Exception:  # deliberado: log e segue (RabbitMQ pode ainda estar subindo)
        logger.warning("Falha ao conectar ao RabbitMQ no startup.", exc_info=True)
    yield
    await event_bus.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API do Motor de Pedidos e Orquestrador de Sagas Distribuídas.",
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

app.include_router(order_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
