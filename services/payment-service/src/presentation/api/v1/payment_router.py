"""Rotas FastAPI de Pagamentos e Caixa — camada fina: valida DTO, chama o
UseCase, devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from restaurant_security.rbac import (
    CASHIER,
    MANAGER,
    RESTAURANT_OWNER,
    WAITER,
    CurrentUser,
    require_role,
    require_tenant_id,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.payment_dtos import (
    CashMovementResponse,
    CashRegisterResponse,
    CloseCashRegisterRequest,
    CustomerCheckoutRequest,
    OpenCashRegisterRequest,
    PaymentResponse,
    ProcessPaymentRequest,
    RegisterCashMovementRequest,
)
from src.application.interfaces.repository_interface import IdempotencyStoreInterface
from src.application.use_cases.close_cash_register import CloseCashRegisterUseCase
from src.application.use_cases.customer_checkout import CustomerCheckoutUseCase
from src.application.use_cases.get_cash_register import (
    GetCashRegisterUseCase,
    GetMyOpenCashRegisterUseCase,
    ListCashMovementsUseCase,
)
from src.application.use_cases.get_payment import GetPaymentUseCase, ListPaymentsUseCase
from src.application.use_cases.open_cash_register import OpenCashRegisterUseCase
from src.application.use_cases.process_payment import ProcessPaymentUseCase
from src.application.use_cases.register_cash_movement import RegisterCashMovementUseCase
from src.application.use_cases.staff_checkout import StaffCheckoutUseCase
from src.config import settings
from src.domain.entities.payment import PaymentStatus
from src.infrastructure.clients.dining_service_client import HttpxDiningServiceClient
from src.infrastructure.clients.order_service_client import HttpxOrderServiceClient
from src.infrastructure.clients.restaurant_service_client import HttpxRestaurantServiceClient
from src.presentation.api.v1.dependencies import (
    cash_movement_repository_for,
    cash_register_repository_for,
    enforce_public_rate_limit,
    get_current_user,
    get_db_session,
    get_dining_service_client,
    get_idempotency_store,
    get_order_service_client,
    get_restaurant_service_client,
    payment_repository_for,
)

router = APIRouter(prefix="/api/v1/payments", tags=["Payments & Cashier"])

_CASHIER_ROLES = (RESTAURANT_OWNER, MANAGER, CASHIER)

# O garçom cobra na mesa com a própria maquininha (cartão) — precisa abrir e
# fechar o caixa dele mesmo, consultá-lo e processar o pagamento pra poder
# fechar a comanda. Não estende a auditoria mais ampla (listar/consultar
# caixas e pagamentos de qualquer operador, lançar sangria/suprimento) —
# isso continua restrito a quem cuida do financeiro do restaurante.
_WAITER_PAYMENT_ROLES = (*_CASHIER_ROLES, WAITER)


@router.post(
    "/cash-registers",
    response_model=CashRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abre um caixa operacional com suprimento inicial (US-05.1)",
)
async def open_cash_register(
    payload: OpenCashRegisterRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_WAITER_PAYMENT_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CashRegisterResponse:
    use_case = OpenCashRegisterUseCase(
        cash_register_repository=cash_register_repository_for(session, current_user.tenant_id),
        cash_movement_repository=cash_movement_repository_for(session, current_user.tenant_id),
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        operator_id=payload.operator_id,
        opening_amount=payload.opening_amount,
    )
    await session.commit()
    return response


@router.get(
    "/cash-registers/mine",
    response_model=CashRegisterResponse | None,
    summary="Caixa aberto do usuário logado, se houver",
)
async def get_my_open_cash_register(
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_WAITER_PAYMENT_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CashRegisterResponse | None:
    use_case = GetMyOpenCashRegisterUseCase(
        cash_register_repository=cash_register_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(operator_id=current_user.user_id)


@router.get(
    "/cash-registers/{cash_register_id}",
    response_model=CashRegisterResponse,
    summary="Consulta um caixa operacional",
)
async def get_cash_register(
    cash_register_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_CASHIER_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CashRegisterResponse:
    use_case = GetCashRegisterUseCase(
        cash_register_repository=cash_register_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(cash_register_id=cash_register_id)


@router.get(
    "/cash-registers/{cash_register_id}/movements",
    response_model=list[CashMovementResponse],
    summary="Histórico de movimentações do caixa (US-05.3)",
)
async def list_cash_movements(
    cash_register_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_CASHIER_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[CashMovementResponse]:
    use_case = ListCashMovementsUseCase(
        cash_movement_repository=cash_movement_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(cash_register_id=cash_register_id)


@router.post(
    "/cash-registers/{cash_register_id}/movements",
    response_model=CashMovementResponse,
    summary="Registra sangria ou suprimento adicional no caixa",
)
async def register_cash_movement(
    cash_register_id: uuid.UUID,
    payload: RegisterCashMovementRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_CASHIER_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CashMovementResponse:
    use_case = RegisterCashMovementUseCase(
        cash_register_repository=cash_register_repository_for(session, current_user.tenant_id),
        cash_movement_repository=cash_movement_repository_for(session, current_user.tenant_id),
    )
    response = await use_case.execute(
        cash_register_id=cash_register_id,
        movement_type=payload.movement_type,
        amount=payload.amount,
        reason=payload.reason,
    )
    await session.commit()
    return response


@router.post(
    "/cash-registers/{cash_register_id}/close",
    response_model=CashRegisterResponse,
    summary="Fechamento cego do caixa, com relatório de divergência (US-05.3)",
)
async def close_cash_register(
    cash_register_id: uuid.UUID,
    payload: CloseCashRegisterRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_WAITER_PAYMENT_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CashRegisterResponse:
    use_case = CloseCashRegisterUseCase(
        cash_register_repository=cash_register_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        cash_register_id=cash_register_id, counted_amount=payload.counted_amount
    )
    await session.commit()
    return response


@router.post(
    "/customer-checkout",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pagamento de autoatendimento do cliente pelo customer-web, sem caixa (público, US-05.4)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def customer_checkout(  # noqa: PLR0913, PLR0917 - dependencies extras (3 clients de outros serviços)
    payload: CustomerCheckoutRequest,
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    dining_service_client: Annotated[HttpxDiningServiceClient, Depends(get_dining_service_client)],
    order_service_client: Annotated[HttpxOrderServiceClient, Depends(get_order_service_client)],
    restaurant_service_client: Annotated[
        HttpxRestaurantServiceClient, Depends(get_restaurant_service_client)
    ],
    idempotency_store: Annotated[IdempotencyStoreInterface, Depends(get_idempotency_store)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PaymentResponse:
    use_case = CustomerCheckoutUseCase(
        process_payment_use_case=ProcessPaymentUseCase(
            payment_repository=payment_repository_for(session, tenant_id),
            cash_register_repository=cash_register_repository_for(session, tenant_id),
            cash_movement_repository=cash_movement_repository_for(session, tenant_id),
            idempotency_store=idempotency_store,
        ),
        dining_service_client=dining_service_client,
        order_service_client=order_service_client,
        restaurant_service_client=restaurant_service_client,
    )
    response = await use_case.execute(
        tenant_id=tenant_id,
        table_number=payload.table_number,
        secret=payload.secret,
        splits=payload.splits,
        idempotency_key=idempotency_key,
        card_last4=payload.card_last4,
        card_holder_name=payload.card_holder_name,
    )
    await session.commit()
    return response


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Processa o pagamento de uma comanda, com divisão entre meios (US-05.2)",
)
async def process_payment(  # noqa: PLR0913, PLR0917 - uma dependency a mais (order_service_client, piso de segurança)
    payload: ProcessPaymentRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_WAITER_PAYMENT_ROLES))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    order_service_client: Annotated[HttpxOrderServiceClient, Depends(get_order_service_client)],
    idempotency_store: Annotated[IdempotencyStoreInterface, Depends(get_idempotency_store)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PaymentResponse:
    use_case = StaffCheckoutUseCase(
        process_payment_use_case=ProcessPaymentUseCase(
            payment_repository=payment_repository_for(session, current_user.tenant_id),
            cash_register_repository=cash_register_repository_for(session, current_user.tenant_id),
            cash_movement_repository=cash_movement_repository_for(session, current_user.tenant_id),
            idempotency_store=idempotency_store,
        ),
        order_service_client=order_service_client,
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        order_id=payload.order_id,
        cash_register_id=payload.cash_register_id,
        command_id=payload.command_id,
        expected_total=payload.expected_total,
        splits=payload.splits,
        idempotency_key=idempotency_key,
        card_last4=payload.card_last4,
        card_holder_name=payload.card_holder_name,
        signature_data=payload.signature_data,
    )
    await session.commit()
    return response


@router.get("", response_model=list[PaymentResponse], summary="Lista pagamentos do tenant")
async def list_payments(
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_CASHIER_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: Annotated[PaymentStatus | None, Query(alias="status")] = None,
    command_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtra pagamentos de uma comanda (Payment por Comanda)"),
    ] = None,
) -> list[PaymentResponse]:
    use_case = ListPaymentsUseCase(
        payment_repository=payment_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(status=status_filter, command_id=command_id)


@router.get("/{payment_id}", response_model=PaymentResponse, summary="Consulta um pagamento")
async def get_payment(
    payment_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_CASHIER_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PaymentResponse:
    use_case = GetPaymentUseCase(
        payment_repository=payment_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(payment_id=payment_id)


@router.get("/health/check", summary="Health Check do Serviço de Pagamentos")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
