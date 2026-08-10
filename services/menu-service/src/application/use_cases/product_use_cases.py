"""Casos de uso de Produtos do Cardápio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.menu_dtos import ProductResponse
from src.application.interfaces.repository_interface import (
    CategoryRepositoryInterface,
    ProductRepositoryInterface,
)
from src.application.interfaces.search_interface import ProductSearchDocument, SearchIndexInterface
from src.domain.entities.product import Product


def _to_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        tenant_id=product.tenant_id,
        category_id=product.category_id,
        name=product.name,
        description=product.description,
        price=product.price,
        cost_price=product.cost_price,
        tax_rate=product.tax_rate,
        photo_url=product.photo_url,
        display_order=product.display_order,
        is_active=product.is_active,
    )


def _to_search_document(product: Product) -> ProductSearchDocument:
    return ProductSearchDocument(
        id=str(product.id),
        tenant_id=str(product.tenant_id),
        name=product.name,
        description=product.description,
        category_id=str(product.category_id),
        price=product.price,
        photo_url=product.photo_url,
    )


@dataclass
class CreateProductUseCase:
    """Cria um produto e o indexa no motor de busca (Meilisearch) pós-commit."""

    product_repository: ProductRepositoryInterface
    category_repository: CategoryRepositoryInterface
    search_index: SearchIndexInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        tenant_id: uuid.UUID,
        category_id: uuid.UUID,
        name: str,
        description: str = "",
        price: float = 0.0,
        cost_price: float = 0.0,
        tax_rate: float = 0.0,
        photo_url: str = "",
        display_order: int = 0,
    ) -> ProductResponse:
        if await self.category_repository.get_by_id(category_id) is None:
            raise ResourceNotFoundException("Category", str(category_id))

        product = Product(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            cost_price=cost_price,
            tax_rate=tax_rate,
            photo_url=photo_url,
            display_order=display_order,
        )
        created = await self.product_repository.add(product)
        await self.search_index.index_product(_to_search_document(created))
        return _to_response(created)


@dataclass
class GetProductUseCase:
    product_repository: ProductRepositoryInterface

    async def execute(self, *, product_id: uuid.UUID) -> ProductResponse:
        product = await self.product_repository.get_by_id(product_id)
        if product is None:
            raise ResourceNotFoundException("Product", str(product_id))
        return _to_response(product)


@dataclass
class ListProductsUseCase:
    product_repository: ProductRepositoryInterface

    async def execute(self, *, category_id: uuid.UUID | None = None) -> list[ProductResponse]:
        products = (
            await self.product_repository.list_by_category(category_id)
            if category_id is not None
            else await self.product_repository.list_all()
        )
        return [_to_response(p) for p in sorted(products, key=lambda p: p.display_order)]


@dataclass
class UpdateProductUseCase:
    """Atualiza preço/descrição de um produto e reindexa no motor de busca."""

    product_repository: ProductRepositoryInterface
    search_index: SearchIndexInterface

    async def execute(
        self, *, product_id: uuid.UUID, name: str, description: str, price: float, is_active: bool
    ) -> ProductResponse:
        product = await self.product_repository.get_by_id(product_id)
        if product is None:
            raise ResourceNotFoundException("Product", str(product_id))

        product.name = name
        product.description = description
        product.price = price
        product.is_active = is_active

        updated = await self.product_repository.save(product)
        await self.search_index.index_product(_to_search_document(updated))
        return _to_response(updated)
