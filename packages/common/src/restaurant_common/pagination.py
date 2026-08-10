"""DTO genérico de paginação usado pelos endpoints de listagem de todos os serviços."""

# ruff: noqa: UP046 -- Pydantic BaseModel genérico usa `Generic[T]`/`TypeVar` clássico
# por compatibilidade ampla com pydantic v2, em vez da sintaxe PEP 695 do Python 3.12.

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope padrão de resposta paginada."""

    items: list[T]
    total: int = Field(..., description="Total de registros disponíveis (sem paginação)")
    limit: int = Field(..., description="Quantidade máxima de itens retornados nesta página")
    offset: int = Field(..., description="Deslocamento a partir do início da coleção")

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total
