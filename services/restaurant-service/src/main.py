"""Ponto de Entrada Principal do Microsserviço de Restaurantes e Branding.

Expõe as APIs REST para cadastro de tenant, consulta pública e atualização
de preferências operacionais e de tema White-Label do restaurante.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from restaurant_common.problem_details import register_exception_handlers
from restaurant_security.tenant_context import TenantContextMiddleware
from src.config import settings
from src.presentation.api.v1.restaurant_router import router as restaurant_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de Gestão de Restaurantes e Temas White-Label para Plataforma SaaS.",
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

app.include_router(restaurant_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
