"""Rotas FastAPI de Salão/Mesas/Comandas/Fila — camada fina: valida DTO, chama
o UseCase, devolve a resposta. Nenhuma regra de negócio aqui (docs/ai/patterns.md)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from restaurant_security.rbac import (
    CASHIER,
    MANAGER,
    RESTAURANT_OWNER,
    WAITER,
    CurrentUser,
    require_role,
    require_tenant_id,
)  # require_tenant_id: rotas públicas do autoatendimento (US-05.4)
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.dining_dtos import (
    AddQueueEntryRequest,
    CommandResponse,
    CreateTableRequest,
    OpenCommandRequest,
    QueueEntryResponse,
    TableQrSecretResponse,
    TableResponse,
    UpdateServiceFeeRequest,
    ValidateQrSecretResponse,
)
from src.application.use_cases.command_use_cases import (
    CloseCommandUseCase,
    CustomerCloseCommandUseCase,
    GetOpenCommandForTableUseCase,
    ListCommandsUseCase,
    OpenCommandUseCase,
    SetCommandServiceFeeUseCase,
)
from src.application.use_cases.queue_use_cases import (
    AddToQueueUseCase,
    CallNextInQueueUseCase,
    ListQueueUseCase,
)
from src.application.use_cases.table_use_cases import (
    CreateTableUseCase,
    ListTablesUseCase,
    MarkTableCleanedUseCase,
    RotateTableQrSecretUseCase,
    ValidateTableQrSecretUseCase,
)
from src.config import settings
from src.domain.entities.command import CommandStatus
from src.presentation.api.v1.dependencies import (
    command_repository_for,
    enforce_public_rate_limit,
    get_current_user,
    get_db_session,
    queue_repository_for,
    table_repository_for,
)

router = APIRouter(prefix="/api/v1/dining", tags=["Dining"])

_STAFF_ROLES = (RESTAURANT_OWNER, MANAGER, WAITER)


@router.post(
    "/tables",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra mesa (Manager/Owner)",
)
async def create_table(
    payload: CreateTableRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, RESTAURANT_OWNER, MANAGER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TableResponse:
    use_case = CreateTableUseCase(
        table_repository=table_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        number=payload.number,
        capacity=payload.capacity,
        qr_code_url=payload.qr_code_url,
    )
    await session.commit()
    return response


@router.get(
    "/tables",
    response_model=list[TableResponse],
    summary="Mapa de mesas em tempo real (equipe autenticada)",
)
async def list_tables(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[TableResponse]:
    use_case = ListTablesUseCase(
        table_repository=table_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute()


@router.post(
    "/tables/{table_id}/mark-cleaned",
    response_model=TableResponse,
    summary="Libera uma mesa 'Aguardando Limpeza' de volta para disponível (Garçom/Manager/Owner)",
)
async def mark_table_cleaned(
    table_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_STAFF_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TableResponse:
    use_case = MarkTableCleanedUseCase(
        table_repository=table_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(table_id=table_id)
    await session.commit()
    return response


@router.post(
    "/tables/{table_id}/qr-secret/rotate",
    response_model=TableQrSecretResponse,
    summary="Gera uma nova secret de QR Code para a mesa, invalidando a anterior (Garçom/Manager/Owner)",
)
async def rotate_table_qr_secret(
    table_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_STAFF_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TableQrSecretResponse:
    use_case = RotateTableQrSecretUseCase(
        table_repository=table_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(table_id=table_id)
    await session.commit()
    return response


@router.get(
    "/tables/{table_number}/qr-secret/validate",
    response_model=ValidateQrSecretResponse,
    summary="Valida a secret de QR Code de uma mesa (público — checagem do cardápio digital)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def validate_table_qr_secret(
    table_number: int,
    secret: Annotated[str, Query(min_length=1)],
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ValidateQrSecretResponse:
    use_case = ValidateTableQrSecretUseCase(
        table_repository=table_repository_for(session, tenant_id)
    )
    return await use_case.execute(table_number=table_number, secret=secret)


@router.get(
    "/tables/{table_number}/open-command",
    response_model=CommandResponse,
    summary="Comanda aberta da mesa, para o autoatendimento do cliente (público, US-05.4)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def get_open_command_for_table(
    table_number: int,
    secret: Annotated[str, Query(min_length=1)],
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CommandResponse:
    use_case = GetOpenCommandForTableUseCase(
        command_repository=command_repository_for(session, tenant_id),
        table_repository=table_repository_for(session, tenant_id),
    )
    return await use_case.execute(table_number=table_number, secret=secret)


@router.post(
    "/commands/open",
    response_model=CommandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abre comanda em uma mesa disponível (Garçom/Manager/Owner)",
)
async def open_command(
    payload: OpenCommandRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_STAFF_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CommandResponse:
    use_case = OpenCommandUseCase(
        command_repository=command_repository_for(session, current_user.tenant_id),
        table_repository=table_repository_for(session, current_user.tenant_id),
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        table_number=payload.table_number,
        customer_name=payload.customer_name,
        waiter_id=current_user.user_id,
        customer_cpf=payload.customer_cpf,
    )
    await session.commit()
    return response


@router.post(
    "/commands/{command_id}/close",
    response_model=CommandResponse,
    summary="Fecha comanda e libera a mesa para limpeza (Garçom/Caixa/Manager/Owner)",
)
async def close_command(
    command_id: uuid.UUID,
    current_user: Annotated[
        CurrentUser, Depends(require_role(get_current_user, *_STAFF_ROLES, CASHIER))
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CommandResponse:
    use_case = CloseCommandUseCase(
        command_repository=command_repository_for(session, current_user.tenant_id),
        table_repository=table_repository_for(session, current_user.tenant_id),
    )
    response = await use_case.execute(command_id=command_id)
    await session.commit()
    return response


@router.post(
    "/commands/{command_id}/customer-close",
    response_model=CommandResponse,
    summary="Fecha a própria comanda no autoatendimento (público, US-05.4 — exige secret da mesa)",
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def customer_close_command(
    command_id: uuid.UUID,
    secret: Annotated[str, Query(min_length=1)],
    tenant_id: Annotated[uuid.UUID, Depends(require_tenant_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CommandResponse:
    use_case = CustomerCloseCommandUseCase(
        command_repository=command_repository_for(session, tenant_id),
        table_repository=table_repository_for(session, tenant_id),
    )
    response = await use_case.execute(command_id=command_id, secret=secret)
    await session.commit()
    return response


@router.patch(
    "/commands/{command_id}/service-fee",
    response_model=CommandResponse,
    summary="Marca/desmarca a cobrança de taxa de serviço na comanda (Garçom/Manager/Owner)",
)
async def set_command_service_fee(
    command_id: uuid.UUID,
    payload: UpdateServiceFeeRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_STAFF_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CommandResponse:
    use_case = SetCommandServiceFeeUseCase(
        command_repository=command_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(command_id=command_id, charged=payload.charged)
    await session.commit()
    return response


@router.get(
    "/commands", response_model=list[CommandResponse], summary="Lista comandas (equipe autenticada)"
)
async def list_commands(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: Annotated[CommandStatus | None, Query(alias="status")] = None,
) -> list[CommandResponse]:
    use_case = ListCommandsUseCase(
        command_repository=command_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute(status=status_filter)


@router.post(
    "/queue",
    response_model=QueueEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona cliente à fila de espera (Garçom/Manager/Owner)",
)
async def add_to_queue(
    payload: AddQueueEntryRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_STAFF_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> QueueEntryResponse:
    use_case = AddToQueueUseCase(
        queue_repository=queue_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute(
        tenant_id=current_user.tenant_id,
        customer_name=payload.customer_name,
        phone=payload.phone,
        party_size=payload.party_size,
    )
    await session.commit()
    return response


@router.get(
    "/queue",
    response_model=list[QueueEntryResponse],
    summary="Consulta fila de espera (equipe autenticada)",
)
async def list_queue(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[QueueEntryResponse]:
    use_case = ListQueueUseCase(
        queue_repository=queue_repository_for(session, current_user.tenant_id)
    )
    return await use_case.execute()


@router.post(
    "/queue/call-next",
    response_model=QueueEntryResponse,
    summary="Chama o próximo da fila (Garçom/Manager/Owner)",
)
async def call_next_in_queue(
    current_user: Annotated[CurrentUser, Depends(require_role(get_current_user, *_STAFF_ROLES))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> QueueEntryResponse:
    use_case = CallNextInQueueUseCase(
        queue_repository=queue_repository_for(session, current_user.tenant_id)
    )
    response = await use_case.execute()
    await session.commit()
    return response


@router.get("/health/check", summary="Health Check do Serviço de Salão")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
