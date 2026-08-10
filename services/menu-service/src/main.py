"""Ponto de Entrada Principal do Microsserviço de Cardápio e Busca Inteligente.

Expõe as APIs REST para o Cardápio Digital e integra com o Meilisearch para
busca em tempo real com tolerância a erros de digitação (Typo Tolerance).
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
from src.presentation.api.v1.dependencies import search_index
from src.presentation.api.v1.menu_router import router as menu_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Busca é um recurso de conveniência (search-as-you-type), não crítico
    # para o funcionamento do serviço — uma falha ao configurar o Meilisearch
    # no boot (ex: container ainda subindo) não deve derrubar o menu-service.
    try:
        await search_index.configure()
    except Exception:  # deliberado: log e segue, ver comentário acima (busca não é crítica)
        logger.warning("Falha ao configurar o índice do Meilisearch no startup.", exc_info=True)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API do Cardápio Digital, Categorias, Produtos e Busca Inteligente (Meilisearch).",
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

app.include_router(menu_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
