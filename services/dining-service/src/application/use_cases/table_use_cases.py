"""Casos de uso de Mesas do Salão."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.dining_dtos import (
    TableQrSecretResponse,
    TableResponse,
    ValidateQrSecretResponse,
)
from src.application.interfaces.repository_interface import TableRepositoryInterface
from src.domain.entities.table import Table, TableStatus
from src.domain.exceptions import (
    DuplicateTableNumberError,
    InvalidOrExpiredQrSecretError,
    TableNotAwaitingCleaningError,
)


def _to_response(table: Table) -> TableResponse:
    return TableResponse(
        id=table.id,
        tenant_id=table.tenant_id,
        number=table.number,
        capacity=table.capacity,
        status=table.status,
        qr_code_url=table.qr_code_url,
    )


@dataclass
class CreateTableUseCase:
    table_repository: TableRepositoryInterface

    async def execute(
        self, *, tenant_id: uuid.UUID, number: int, capacity: int, qr_code_url: str = ""
    ) -> TableResponse:
        if await self.table_repository.get_by_number(number) is not None:
            raise DuplicateTableNumberError(number)

        table = Table(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            number=number,
            capacity=capacity,
            qr_code_url=qr_code_url,
        )
        created = await self.table_repository.add(table)
        return _to_response(created)


@dataclass
class ListTablesUseCase:
    table_repository: TableRepositoryInterface

    async def execute(self) -> list[TableResponse]:
        tables = await self.table_repository.list_all()
        return [_to_response(t) for t in sorted(tables, key=lambda t: t.number)]


@dataclass
class MarkTableCleanedUseCase:
    """Libera uma mesa `WAITING_CLEANING` de volta pra `AVAILABLE` — gap
    encontrado em 2026-08-06: a transição já era válida no domínio
    (`Table.transition_to`), mas nenhum endpoint a acionava, então toda
    comanda encerrada prendia a mesa pra sempre (US-03.5)."""

    table_repository: TableRepositoryInterface

    async def execute(self, *, table_id: uuid.UUID) -> TableResponse:
        table = await self.table_repository.get_by_id(table_id)
        if table is None:
            raise ResourceNotFoundException("Table", str(table_id))
        if table.status != TableStatus.WAITING_CLEANING:
            raise TableNotAwaitingCleaningError(table.number)

        table.transition_to(TableStatus.AVAILABLE)
        updated = await self.table_repository.save(table)
        return _to_response(updated)


@dataclass
class RotateTableQrSecretUseCase:
    """Gera uma nova secret para o QR Code da mesa, invalidando a anterior —
    acionada explicitamente pela tela do `admin-web` (ex: abrir uma nova
    mesa, ou forçar um novo código por suspeita de vazamento). A rotação
    automática de fim de ciclo acontece em `CloseCommandUseCase`, não aqui."""

    table_repository: TableRepositoryInterface

    async def execute(self, *, table_id: uuid.UUID) -> TableQrSecretResponse:
        table = await self.table_repository.get_by_id(table_id)
        if table is None:
            raise ResourceNotFoundException("Table", str(table_id))

        table.rotate_qr_secret()
        await self.table_repository.save(table)

        if table.active_qr_secret is None or table.qr_secret_expires_at is None:
            msg = "Table.active_qr_secret/qr_secret_expires_at deveriam estar preenchidos após rotate_qr_secret()."
            raise RuntimeError(msg)
        return TableQrSecretResponse(
            secret=table.active_qr_secret, expires_at=table.qr_secret_expires_at
        )


@dataclass
class ValidateTableQrSecretUseCase:
    """Valida a secret rotativa de uma mesa — chamado pelo `customer-web`
    antes de liberar o cardápio digital (QR Code passou a ser obrigatório)."""

    table_repository: TableRepositoryInterface

    async def execute(self, *, table_number: int, secret: str) -> ValidateQrSecretResponse:
        table = await self.table_repository.get_by_number(table_number)
        if table is None or not table.is_qr_secret_valid(secret):
            raise InvalidOrExpiredQrSecretError(table_number)
        return ValidateQrSecretResponse(valid=True, table_id=table.id)
