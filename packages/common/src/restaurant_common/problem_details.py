"""RFC 7807 Exception Handler (docs/ai/patterns.md — padrão obrigatório).

Converte qualquer `BaseDomainException` (e subclasses) lançada em um caso de
uso ou repositório em uma resposta `application/problem+json` padronizada,
em vez de deixar o FastAPI vazar um erro 500 genérico ou exigir que cada
endpoint capture exceções manualmente (o que violaria a regra de "Fat
Controllers" de `docs/ai/patterns.md`).

Uso em cada `src/main.py`:

    from restaurant_common.problem_details import register_exception_handlers

    app = FastAPI(...)
    register_exception_handlers(app)
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from restaurant_core.exceptions import BaseDomainException


class ProblemDetails(BaseModel):
    """Corpo de resposta padronizado conforme RFC 7807."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str
    code: str
    errors: dict[str, Any] | None = None


def register_exception_handlers(app: FastAPI) -> None:
    """Registra o handler global de `BaseDomainException` na aplicação FastAPI."""

    @app.exception_handler(BaseDomainException)
    async def _handle_domain_exception(request: Request, exc: BaseDomainException) -> JSONResponse:
        problem = ProblemDetails(
            title=type(exc).__name__,
            status=exc.status_code,
            detail=exc.message,
            instance=str(request.url),
            code=exc.code,
            errors=exc.details or None,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(exclude_none=True),
            media_type="application/problem+json",
        )
