"""Caso de uso: busca inteligente do cardápio digital (ADR-006 — Meilisearch)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.application.dtos.menu_dtos import ProductSearchResultResponse
from src.application.interfaces.search_interface import SearchIndexInterface


@dataclass
class SearchProductsUseCase:
    search_index: SearchIndexInterface

    async def execute(
        self, *, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[ProductSearchResultResponse]:
        results = await self.search_index.search(tenant_id=tenant_id, query=query, limit=limit)
        return [
            ProductSearchResultResponse(
                id=uuid.UUID(doc["id"]),
                name=doc["name"],
                description=doc["description"],
                category_id=uuid.UUID(doc["category_id"]),
                price=doc["price"],
                photo_url=doc["photo_url"],
            )
            for doc in results
        ]
