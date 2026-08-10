"""Contrato do repositório de restaurantes (Repository Pattern com Interfaces).

Diferente dos demais serviços, este repositório NÃO é tenant-scoped: cada
`Restaurant` É um tenant, então as buscas são feitas diretamente pelo `id`
(gerenciado pelo `restaurant-service`, que administra a lista completa de
tenants da plataforma) ou pelo `slug` público.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.entities.restaurant import Restaurant


class RestaurantRepositoryInterface(Protocol):
    """Operações de persistência necessárias pelos casos de uso de Restaurantes."""

    async def get_by_id(self, restaurant_id: uuid.UUID) -> Restaurant | None: ...

    async def get_by_slug(self, slug: str) -> Restaurant | None: ...

    async def slug_exists(self, slug: str) -> bool: ...

    async def add(self, restaurant: Restaurant) -> Restaurant: ...

    async def save(self, restaurant: Restaurant) -> Restaurant: ...
