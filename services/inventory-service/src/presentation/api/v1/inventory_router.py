"""Rotas FastAPI de Estoque — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from restaurant_security.rbac import (
    MANAGER,
    RESTAURANT_OWNER,
    CurrentUser,
    require_role,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.inventory_dtos import (
    AdjustStockCountRequest,
    CreateInventoryItemRequest,
    CreateSupplierRequest,
    InventoryItemResponse,
    RecipeResponse,
    RegisterStockMovementRequest,
    StockMovementResponse,
    SupplierResponse,
    UpsertRecipeRequest,
)
from src.application.use_cases.adjust_stock_count import AdjustStockCountUseCase
from src.application.use_cases.create_inventory_item import CreateInventoryItemUseCase
from src.application.use_cases.create_supplier import CreateSupplierUseCase, ListSuppliersUseCase
from src.application.use_cases.get_recipe import GetRecipeUseCase
from src.application.use_cases.list_inventory_items import ListInventoryItemsUseCase
from src.application.use_cases.register_stock_movement import RegisterStockMovementUseCase
from src.application.use_cases.upsert_recipe import UpsertRecipeUseCase
from src.config import settings
from src.presentation.api.v1.dependencies import (
    get_current_user,
    get_db_session,
    inventory_item_repository_for,
    recipe_repository_for,
    stock_movement_repository_for,
    supplier_repository_for,
)

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])

_INVENTORY_ROLES = (RESTAURANT_OWNER, MANAGER)


@router.post(
    "/items",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo insumo",
)
async def create_inventory_item(
    payload: CreateInventoryItemRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_INVENTORY_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryItemResponse:
    use_case = CreateInventoryItemUseCase(
        inventory_item_repository=inventory_item_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        unit=payload.unit,
        initial_quantity=payload.initial_quantity,
        minimum_quantity=payload.minimum_quantity,
        supplier_id=payload.supplier_id,
    )
    await session.commit()
    return response


@router.get(
    "/items", response_model=list[InventoryItemResponse], summary="Lista os insumos em estoque"
)
async def list_inventory_items(
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_INVENTORY_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    only_below_minimum: Annotated[bool, Query()] = False,
) -> list[InventoryItemResponse]:
    use_case = ListInventoryItemsUseCase(
        inventory_item_repository=inventory_item_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(only_below_minimum=only_below_minimum)


@router.post(
    "/items/{inventory_item_id}/movements",
    response_model=StockMovementResponse,
    summary="Registra uma movimentação manual de estoque (entrada, perda, devolução)",
)
async def register_stock_movement(
    inventory_item_id: uuid.UUID,
    payload: RegisterStockMovementRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_INVENTORY_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StockMovementResponse:
    use_case = RegisterStockMovementUseCase(
        inventory_item_repository=inventory_item_repository_for(session, current_user.tenant_id),
        stock_movement_repository=stock_movement_repository_for(session, current_user.tenant_id),
    )
    response = await use_case.execute(
        inventory_item_id=inventory_item_id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        reason=payload.reason,
    )
    await session.commit()
    return response


@router.post(
    "/items/{inventory_item_id}/count",
    response_model=StockMovementResponse,
    summary="Registra uma contagem de inventário, ajustando o estoque para o valor contado",
)
async def adjust_stock_count(
    inventory_item_id: uuid.UUID,
    payload: AdjustStockCountRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_INVENTORY_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StockMovementResponse:
    use_case = AdjustStockCountUseCase(
        inventory_item_repository=inventory_item_repository_for(session, current_user.tenant_id),
        stock_movement_repository=stock_movement_repository_for(session, current_user.tenant_id),
    )
    response = await use_case.execute(
        inventory_item_id=inventory_item_id,
        counted_quantity=payload.counted_quantity,
        reason=payload.reason,
    )
    await session.commit()
    return response


@router.post(
    "/suppliers",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo fornecedor",
)
async def create_supplier(
    payload: CreateSupplierRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_INVENTORY_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupplierResponse:
    use_case = CreateSupplierUseCase(
        supplier_repository=supplier_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        contact_phone=payload.contact_phone,
        contact_email=payload.contact_email,
    )
    await session.commit()
    return response


@router.get("/suppliers", response_model=list[SupplierResponse], summary="Lista os fornecedores")
async def list_suppliers(
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_INVENTORY_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SupplierResponse]:
    use_case = ListSuppliersUseCase(
        supplier_repository=supplier_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute()


@router.put(
    "/recipes",
    response_model=RecipeResponse,
    summary="Cria ou atualiza a ficha técnica de um produto (US-02.4)",
)
async def upsert_recipe(
    payload: UpsertRecipeRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_INVENTORY_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecipeResponse:
    use_case = UpsertRecipeUseCase(
        recipe_repository=recipe_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id, product_id=payload.product_id, items=payload.items
    )
    await session.commit()
    return response


@router.get(
    "/recipes/{product_id}",
    response_model=RecipeResponse,
    summary="Consulta a ficha técnica de um produto",
)
async def get_recipe(
    product_id: uuid.UUID,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_INVENTORY_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecipeResponse:
    use_case = GetRecipeUseCase(
        recipe_repository=recipe_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(product_id=product_id)


@router.get("/health/check", summary="Health Check do Serviço de Estoque")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
