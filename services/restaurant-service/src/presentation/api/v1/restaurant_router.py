"""Rotas FastAPI de Restaurantes — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from restaurant_security.rbac import MANAGER, RESTAURANT_OWNER, CurrentUser, require_role
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.restaurant_dtos import (
    CreateRestaurantRequest,
    RestaurantResponse,
    UpdateBrandingRequest,
    UpdateRestaurantRequest,
)
from src.application.use_cases.create_restaurant import CreateRestaurantUseCase
from src.application.use_cases.get_restaurant import (
    GetRestaurantByIdUseCase,
    GetRestaurantBySlugUseCase,
)
from src.application.use_cases.update_branding import UpdateBrandingUseCase
from src.application.use_cases.update_restaurant import UpdateRestaurantUseCase
from src.config import settings
from src.presentation.api.v1.dependencies import (
    enforce_public_rate_limit,
    get_current_user,
    get_db_session,
    restaurant_repository_for,
)

router = APIRouter(prefix="/api/v1/restaurants", tags=["Restaurants"])


@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastro público de um novo restaurante (bootstrap de tenant)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def create_restaurant(
    payload: CreateRestaurantRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RestaurantResponse:
    use_case = CreateRestaurantUseCase(restaurant_repository=restaurant_repository_for(session))
    response = await use_case.execute(
        slug=payload.slug,
        trade_name=payload.trade_name,
        legal_name=payload.legal_name,
        cnpj=payload.cnpj,
        phone=payload.phone,
        currency=payload.currency,
        service_fee_percent=payload.service_fee_percent,
    )
    await session.commit()
    return response


@router.get(
    "/by-slug/{slug}",
    response_model=RestaurantResponse,
    summary="Consulta pública por slug",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def get_restaurant_by_slug(
    slug: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RestaurantResponse:
    use_case = GetRestaurantBySlugUseCase(restaurant_repository=restaurant_repository_for(session))
    return await use_case.execute(slug=slug)


@router.get(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Consulta pública por ID",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def get_restaurant_by_id(
    restaurant_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RestaurantResponse:
    use_case = GetRestaurantByIdUseCase(restaurant_repository=restaurant_repository_for(session))
    return await use_case.execute(restaurant_id=restaurant_id)


@router.patch(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Atualiza dados operacionais (apenas o próprio Owner/Manager)",
)
async def update_restaurant(
    restaurant_id: uuid.UUID,
    payload: UpdateRestaurantRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RestaurantResponse:
    use_case = UpdateRestaurantUseCase(restaurant_repository=restaurant_repository_for(session))
    response = await use_case.execute(
        restaurant_id=restaurant_id,
        acting_tenant_id=current_user.tenant_id,
        trade_name=payload.trade_name,
        phone=payload.phone,
        currency=payload.currency,
        service_fee_percent=payload.service_fee_percent,
    )
    await session.commit()
    return response


@router.put(
    "/{restaurant_id}/branding",
    response_model=RestaurantResponse,
    summary="Atualiza tema/branding White-Label (apenas o próprio Owner/Manager)",
)
async def update_branding(
    restaurant_id: uuid.UUID,
    payload: UpdateBrandingRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RestaurantResponse:
    use_case = UpdateBrandingUseCase(restaurant_repository=restaurant_repository_for(session))
    response = await use_case.execute(
        restaurant_id=restaurant_id, acting_tenant_id=current_user.tenant_id, payload=payload
    )
    await session.commit()
    return response


@router.get("/health/check", summary="Health Check do Serviço de Restaurantes")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
