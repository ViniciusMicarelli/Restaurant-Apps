"""Rotas FastAPI de Autenticação — camada fina: valida DTO, chama o UseCase,
devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from restaurant_security.rbac import MANAGER, RESTAURANT_OWNER, CurrentUser, require_role
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.user_dtos import (
    LoginWithPasswordRequest,
    LoginWithPinRequest,
    RefreshTokenRequest,
    RegisterEmployeeRequest,
    RegisterOwnerRequest,
    RegisterUserResponse,
    TokenResponse,
    UserProfileResponse,
)
from src.application.interfaces.repository_interface import TokenBlacklistInterface
from src.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.application.use_cases.login_with_password import LoginWithPasswordUseCase
from src.application.use_cases.login_with_pin import LoginWithPinUseCase
from src.application.use_cases.logout_user import LogoutUserUseCase
from src.application.use_cases.refresh_access_token import RefreshAccessTokenUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.config import settings
from src.domain.entities.user import UserRole
from src.presentation.api.v1.dependencies import (
    enforce_login_rate_limit,
    get_current_user,
    get_db_session,
    get_token_blacklist,
    get_user_lookup_repository,
    user_repository_for,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/register-owner",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastro do primeiro usuário (dono) de um restaurante novo",
)
async def register_owner(
    payload: RegisterOwnerRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegisterUserResponse:
    """Único endpoint de escrita não-autenticado do serviço.

    Chamado uma única vez logo após o `restaurant-service` criar o tenant —
    ainda não existe ninguém autenticado para criar o primeiro usuário.
    """
    use_case = RegisterUserUseCase(
        user_repository=user_repository_for(session, payload.tenant_id),
        user_lookup=get_user_lookup_repository(session),
    )
    response = await use_case.execute(
        tenant_id=payload.tenant_id,
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=UserRole.RESTAURANT_OWNER,
    )
    await session.commit()
    return response


@router.post(
    "/employees",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastro de funcionário por um Owner/Manager autenticado",
)
async def register_employee(
    payload: RegisterEmployeeRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegisterUserResponse:
    """`tenant_id` vem sempre do JWT do chamador — nunca do corpo da requisição (IDOR)."""
    use_case = RegisterUserUseCase(
        user_repository=user_repository_for(session, current_user.tenant_id),
        user_lookup=get_user_lookup_repository(session),
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
        pin=payload.pin,
    )
    await session.commit()
    return response


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login com e-mail e senha",
    dependencies=[Depends(enforce_login_rate_limit)],
)
async def login_with_password(
    payload: LoginWithPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    use_case = LoginWithPasswordUseCase(
        user_lookup=get_user_lookup_repository(session),
        jwt_secret_key=settings.jwt_secret_key.get_secret_value(),
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )
    return await use_case.execute(email=payload.email, password=payload.password)


@router.post(
    "/login-pin",
    response_model=TokenResponse,
    summary="Login rápido por PIN (Garçom/Caixa/Cozinha)",
    dependencies=[Depends(enforce_login_rate_limit)],
)
async def login_with_pin(
    payload: LoginWithPinRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    use_case = LoginWithPinUseCase(
        user_repository=user_repository_for(session, payload.tenant_id),
        jwt_secret_key=settings.jwt_secret_key.get_secret_value(),
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )
    return await use_case.execute(pin=payload.pin)


@router.post(
    "/refresh", response_model=TokenResponse, summary="Renova o access token via refresh token"
)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    token_blacklist: Annotated[TokenBlacklistInterface, Depends(get_token_blacklist)],
) -> TokenResponse:
    use_case = RefreshAccessTokenUseCase(
        user_lookup=get_user_lookup_repository(session),
        token_blacklist=token_blacklist,
        jwt_secret_key=settings.jwt_secret_key.get_secret_value(),
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )
    return await use_case.execute(refresh_token=payload.refresh_token)


@router.post(
    "/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoga o access token corrente"
)
async def logout(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    token_blacklist: Annotated[TokenBlacklistInterface, Depends(get_token_blacklist)],
) -> None:
    use_case = LogoutUserUseCase(token_blacklist=token_blacklist)
    await use_case.execute(jti=current_user.jti, expires_at=current_user.expires_at)


@router.get("/me", response_model=UserProfileResponse, summary="Perfil do usuário autenticado")
async def get_my_profile(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserProfileResponse:
    use_case = GetUserProfileUseCase(
        user_repository=user_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(user_id=current_user.user_id)


@router.get("/health", summary="Health Check do Serviço de Auth")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
