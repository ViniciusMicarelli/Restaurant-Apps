"""Rotas FastAPI de Marketing — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from restaurant_security.rbac import (
    CASHIER,
    MANAGER,
    RESTAURANT_OWNER,
    WAITER,
    CurrentUser,
    require_role,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.marketing_dtos import (
    ApplyCouponRequest,
    ApplyCouponResponse,
    CouponResponse,
    CreateCouponRequest,
)
from src.application.use_cases.apply_coupon import ApplyCouponUseCase
from src.application.use_cases.create_coupon import CreateCouponUseCase, ListCouponsUseCase
from src.config import settings
from src.presentation.api.v1.dependencies import (
    coupon_repository_for,
    get_current_user,
    get_db_session,
)

router = APIRouter(prefix="/api/v1/marketing", tags=["Marketing"])

_MANAGE_COUPON_ROLES = (RESTAURANT_OWNER, MANAGER)
_APPLY_COUPON_ROLES = (RESTAURANT_OWNER, MANAGER, CASHIER, WAITER)


@router.post(
    "/coupons",
    response_model=CouponResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo cupom de desconto",
)
async def create_coupon(
    payload: CreateCouponRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_MANAGE_COUPON_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CouponResponse:
    use_case = CreateCouponUseCase(
        coupon_repository=coupon_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        code=payload.code,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        max_uses=payload.max_uses,
    )
    await session.commit()
    return response


@router.get("/coupons", response_model=list[CouponResponse], summary="Lista os cupons do tenant")
async def list_coupons(
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_MANAGE_COUPON_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[CouponResponse]:
    use_case = ListCouponsUseCase(
        coupon_repository=coupon_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute()


@router.post(
    "/coupons/apply",
    response_model=ApplyCouponResponse,
    summary="Valida e aplica um cupom sobre o total de uma comanda",
)
async def apply_coupon(
    payload: ApplyCouponRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_APPLY_COUPON_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplyCouponResponse:
    use_case = ApplyCouponUseCase(
        coupon_repository=coupon_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(code=payload.code, order_total=payload.order_total)
    await session.commit()
    return response


@router.get("/health/check", summary="Health Check do Serviço de Marketing")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
