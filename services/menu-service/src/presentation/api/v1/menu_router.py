"""Rotas FastAPI do Cardápio — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md).

Rotas de leitura (`GET`) são públicas (cardápio digital via QR Code, sem
login) mas continuam escopadas por tenant via `require_tenant_id`
(`TenantContextMiddleware` resolve o tenant do JWT ou do header
`X-Tenant-Id`). Rotas de escrita exigem `MANAGER`/`RESTAURANT_OWNER`.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from restaurant_security.rbac import (
    MANAGER,
    RESTAURANT_OWNER,
    CurrentUser,
    require_role,
    require_tenant_id,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.menu_dtos import (
    AddonGroupResponse,
    CategoryResponse,
    CreateAddonGroupRequest,
    CreateCategoryRequest,
    CreateProductRequest,
    ProductResponse,
    ProductSearchResultResponse,
    UpdateProductRequest,
)
from src.application.interfaces.search_interface import SearchIndexInterface
from src.application.use_cases.addon_group_use_cases import (
    CreateAddonGroupUseCase,
    ListAddonGroupsUseCase,
)
from src.application.use_cases.category_use_cases import (
    CreateCategoryUseCase,
    ListCategoriesUseCase,
)
from src.application.use_cases.product_use_cases import (
    CreateProductUseCase,
    GetProductUseCase,
    ListProductsUseCase,
    UpdateProductUseCase,
)
from src.application.use_cases.search_products import SearchProductsUseCase
from src.config import settings
from src.presentation.api.v1.dependencies import (
    addon_group_repository_for,
    category_repository_for,
    enforce_public_rate_limit,
    get_current_user,
    get_db_session,
    get_search_index,
    product_repository_for,
)

router = APIRouter(prefix="/api/v1/menu", tags=["Menu"])


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria categoria (Manager/Owner)",
)
async def create_category(
    payload: CreateCategoryRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CategoryResponse:
    use_case = CreateCategoryUseCase(
        category_repository=category_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id, name=payload.name, display_order=payload.display_order
    )
    await session.commit()
    return response


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="Lista categorias (público, escopo do tenant)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def list_categories(
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[CategoryResponse]:
    use_case = ListCategoriesUseCase(
        category_repository=category_repository_for(session, tenant_id)
    )
    return await use_case.execute()


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria produto (Manager/Owner)",
)
async def create_product(
    payload: CreateProductRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    search_index: Annotated[SearchIndexInterface, Depends(get_search_index)],
) -> ProductResponse:
    use_case = CreateProductUseCase(
        product_repository=product_repository_for(session, current_user.tenant_id),
        category_repository=category_repository_for(session, current_user.tenant_id),
        search_index=search_index,
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        cost_price=payload.cost_price,
        tax_rate=payload.tax_rate,
        photo_url=payload.photo_url,
        display_order=payload.display_order,
    )
    await session.commit()
    return response


@router.get(
    "/products",
    response_model=list[ProductResponse],
    summary="Lista produtos (público, escopo do tenant)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def list_products(
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    category_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[ProductResponse]:
    use_case = ListProductsUseCase(product_repository=product_repository_for(session, tenant_id))
    return await use_case.execute(category_id=category_id)


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Consulta produto (público, escopo do tenant)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def get_product(
    product_id: uuid.UUID,
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProductResponse:
    use_case = GetProductUseCase(product_repository=product_repository_for(session, tenant_id))
    return await use_case.execute(product_id=product_id)


@router.patch(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Atualiza produto (Manager/Owner)",
)
async def update_product(
    product_id: uuid.UUID,
    payload: UpdateProductRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    search_index: Annotated[SearchIndexInterface, Depends(get_search_index)],
) -> ProductResponse:
    use_case = UpdateProductUseCase(
        product_repository=product_repository_for(session, current_user.tenant_id),
        search_index=search_index,
    )
    response = await use_case.execute(
        product_id=product_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        is_active=payload.is_active,
    )
    await session.commit()
    return response


@router.post(
    "/addon-groups",
    response_model=AddonGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria grupo de adicionais (Manager/Owner)",
)
async def create_addon_group(
    payload: CreateAddonGroupRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AddonGroupResponse:
    use_case = CreateAddonGroupUseCase(
        addon_group_repository=addon_group_repository_for(session, current_user.tenant_id),
        product_repository=product_repository_for(session, current_user.tenant_id),
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        product_id=payload.product_id,
        name=payload.name,
        min_selections=payload.min_selections,
        max_selections=payload.max_selections,
        options=payload.options,
    )
    await session.commit()
    return response


@router.get(
    "/products/{product_id}/addon-groups",
    response_model=list[AddonGroupResponse],
    summary="Lista grupos de adicionais de um produto (público, escopo do tenant)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def list_addon_groups(
    product_id: uuid.UUID,
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AddonGroupResponse]:
    use_case = ListAddonGroupsUseCase(
        addon_group_repository=addon_group_repository_for(session, tenant_id)
    )
    return await use_case.execute(product_id=product_id)


@router.get(
    "/search",
    response_model=list[ProductSearchResultResponse],
    summary="Busca inteligente do cardápio (Meilisearch)",
)
async def search_products(
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    search_index: Annotated[SearchIndexInterface, Depends(get_search_index)],
    q: str = Query(..., min_length=1, max_length=100),
) -> list[ProductSearchResultResponse]:
    use_case = SearchProductsUseCase(search_index=search_index)
    return await use_case.execute(tenant_id=tenant_id, query=q)


@router.get("/health/check", summary="Health Check do Serviço de Cardápio")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
