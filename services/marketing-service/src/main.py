"""Ponto de Entrada Principal do Microsserviço de Marketing & Fidelidade.

Escopo Tier B (base sólida): cadastro e aplicação de cupons de desconto
(`Coupon`). Programa de fidelidade (`LoyaltyAccount`/`LoyaltyTransaction`)
fica para uma fase futura, conforme docs/modules/module_breakdown.md §10.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from restaurant_common.problem_details import register_exception_handlers
from restaurant_security.tenant_context import TenantContextMiddleware
from src.config import settings
from src.presentation.api.v1.marketing_router import router as marketing_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de Marketing — cupons de desconto.",
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

app.include_router(marketing_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
