"""Contrato do índice de busca do cardápio digital (ADR-006 — Meilisearch)."""

from __future__ import annotations

import uuid
from typing import Protocol, TypedDict


class ProductSearchDocument(TypedDict):
    """Documento indexado no motor de busca (Meilisearch em produção)."""

    id: str
    tenant_id: str
    name: str
    description: str
    category_id: str
    price: float
    photo_url: str


class SearchIndexInterface(Protocol):
    """Abstração sobre o motor de busca — permite trocar Meilisearch por um fake em testes."""

    async def index_product(self, document: ProductSearchDocument) -> None: ...

    async def remove_product(self, product_id: uuid.UUID) -> None: ...

    async def search(
        self, *, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[ProductSearchDocument]: ...
