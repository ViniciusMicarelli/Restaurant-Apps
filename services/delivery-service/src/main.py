"""Ponto de Entrada Principal do Microsserviço de Delivery & Retirada.

Rastreia o ciclo de vida de entregas próprias. Escopo Tier B (base sólida):
o ponto de extensão para integrações reais com iFood/Rappi já existe
(`ExternalDeliveryProviderInterface`), mas não é implementado nesta fase.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from restaurant_common.problem_details import register_exception_handlers
from restaurant_security.tenant_context import TenantContextMiddleware
from src.config import settings
from src.presentation.api.v1.delivery_router import router as delivery_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de Delivery & Retirada — rastreio de entregas próprias.",
    docs_url="/docs",
    redoc_url="/redoc",
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

app.include_router(delivery_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
