"""Implementação real de `SearchIndexInterface` sobre Meilisearch (ADR-006).

Índice único `products`, filtrado por `tenant_id` em toda consulta —
mesma disciplina de tenant scoping aplicada às queries SQL (nunca remover).
"""

from __future__ import annotations

import uuid
from typing import Any

import meilisearch_python_sdk as meilisearch
from src.application.interfaces.search_interface import ProductSearchDocument

_INDEX_NAME = "products"
_SEARCHABLE_ATTRIBUTES: list[str] = ["name", "description"]
_FILTERABLE_ATTRIBUTES: list[Any] = ["tenant_id", "category_id"]


class MeilisearchProductIndex:
    """Cliente Meilisearch para busca *search-as-you-type* do cardápio digital."""

    def __init__(self, url: str, master_key: str) -> None:
        self._client = meilisearch.AsyncClient(url, master_key)

    async def configure(self) -> None:
        """Aplica a configuração do índice (campos buscáveis/filtráveis).

        Chamado uma única vez no startup do serviço (`main.py`) — não a cada
        indexação, para não gerar uma task de configuração no Meilisearch a
        cada produto criado/atualizado.
        """
        index = self._client.index(_INDEX_NAME)
        await index.update_searchable_attributes(_SEARCHABLE_ATTRIBUTES)
        await index.update_filterable_attributes(_FILTERABLE_ATTRIBUTES)

    async def index_product(self, document: ProductSearchDocument) -> None:
        index = self._client.index(_INDEX_NAME)
        await index.add_documents([dict(document)], primary_key="id")

    async def remove_product(self, product_id: uuid.UUID) -> None:
        index = self._client.index(_INDEX_NAME)
        await index.delete_document(str(product_id))

    async def search(
        self, *, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[ProductSearchDocument]:
        index = self._client.index(_INDEX_NAME)
        result = await index.search(query, filter=f"tenant_id = {tenant_id}", limit=limit)
        return [
            ProductSearchDocument(
                id=hit["id"],
                tenant_id=hit["tenant_id"],
                name=hit["name"],
                description=hit["description"],
                category_id=hit["category_id"],
                price=hit["price"],
                photo_url=hit["photo_url"],
            )
            for hit in result.hits
        ]
