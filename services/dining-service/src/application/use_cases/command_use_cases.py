"""Casos de uso de Comandas (abertura/fechamento de sessão de consumo em uma mesa)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.dining_dtos import CommandResponse
from src.application.interfaces.repository_interface import (
    CommandRepositoryInterface,
    TableRepositoryInterface,
)
from src.domain.entities.command import Command, CommandStatus
from src.domain.entities.table import TableStatus
from src.domain.exceptions import InvalidOrExpiredQrSecretError, TableNotAvailableError


def _to_response(command: Command) -> CommandResponse:
    return CommandResponse(
        id=command.id,
        tenant_id=command.tenant_id,
        table_id=command.table_id,
        customer_name=command.customer_name,
        customer_cpf=command.customer_cpf,
        waiter_id=command.waiter_id,
        status=command.status,
        service_fee_charged=command.service_fee_charged,
        opened_at=command.opened_at,
        closed_at=command.closed_at,
    )


@dataclass
class OpenCommandUseCase:
    """Abre uma comanda em uma mesa disponível, transicionando-a para `OCCUPIED`."""

    command_repository: CommandRepositoryInterface
    table_repository: TableRepositoryInterface

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        table_number: int,
        customer_name: str,
        waiter_id: uuid.UUID,
        customer_cpf: str | None = None,
    ) -> CommandResponse:
        table = await self.table_repository.get_by_number(table_number)
        if table is None:
            raise ResourceNotFoundException("Table", str(table_number))
        if table.status != TableStatus.AVAILABLE:
            raise TableNotAvailableError(table_number)

        table.transition_to(TableStatus.OCCUPIED)
        await self.table_repository.save(table)

        command = Command(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            table_id=table.id,
            customer_name=customer_name,
            customer_cpf=customer_cpf,
            waiter_id=waiter_id,
        )
        created = await self.command_repository.add(command)
        return _to_response(created)


@dataclass
class CloseCommandUseCase:
    """Fecha uma comanda aberta, transicionando a mesa para `WAITING_CLEANING`
    e rotacionando a secret do QR Code da mesa — o link que os clientes dessa
    comanda usaram pra abrir o cardápio deixa de funcionar no instante em que
    a mesa é encerrada, então quem já saiu não consegue pedir em nome do
    próximo grupo que sentar ali (ver `Table.rotate_qr_secret`)."""

    command_repository: CommandRepositoryInterface
    table_repository: TableRepositoryInterface

    async def execute(self, *, command_id: uuid.UUID) -> CommandResponse:
        command = await self.command_repository.get_by_id(command_id)
        if command is None:
            raise ResourceNotFoundException("Command", str(command_id))

        command.close()
        updated = await self.command_repository.save(command)

        table = await self.table_repository.get_by_id(command.table_id)
        if table is not None and table.status == TableStatus.OCCUPIED:
            table.transition_to(TableStatus.WAITING_CLEANING)
            table.rotate_qr_secret()
            await self.table_repository.save(table)

        return _to_response(updated)


@dataclass
class GetOpenCommandForTableUseCase:
    """Retorna a comanda aberta de uma mesa para o próprio cliente
    (autoatendimento, US-05.4) — exige a mesma secret de QR Code usada para
    abrir o cardápio digital, senão qualquer pessoa que soubesse o
    `tenant_id` (não secreto) poderia inspecionar comandas de outras mesas."""

    command_repository: CommandRepositoryInterface
    table_repository: TableRepositoryInterface

    async def execute(self, *, table_number: int, secret: str) -> CommandResponse:
        table = await self.table_repository.get_by_number(table_number)
        if table is None or not table.is_qr_secret_valid(secret):
            raise InvalidOrExpiredQrSecretError(table_number)

        command = await self.command_repository.get_open_command_for_table(table.id)
        if command is None:
            raise ResourceNotFoundException("Command", f"open command for table {table_number}")
        return _to_response(command)


@dataclass
class CustomerCloseCommandUseCase:
    """Fecha a própria comanda pelo autoatendimento do cliente (US-05.4) —
    mesma lógica de `CloseCommandUseCase`, mas autorizada pela secret de QR
    Code da mesa (chamada por um cliente anônimo, sem papel de equipe)."""

    command_repository: CommandRepositoryInterface
    table_repository: TableRepositoryInterface

    async def execute(self, *, command_id: uuid.UUID, secret: str) -> CommandResponse:
        command = await self.command_repository.get_by_id(command_id)
        if command is None:
            raise ResourceNotFoundException("Command", str(command_id))

        table = await self.table_repository.get_by_id(command.table_id)
        if table is None:
            raise ResourceNotFoundException("Table", str(command.table_id))
        if not table.is_qr_secret_valid(secret):
            raise InvalidOrExpiredQrSecretError(table.number)

        return await CloseCommandUseCase(
            command_repository=self.command_repository,
            table_repository=self.table_repository,
        ).execute(command_id=command_id)


@dataclass
class SetCommandServiceFeeUseCase:
    """Marca/desmarca a cobrança de taxa de serviço numa comanda — responsabilidade
    do garçom, pode ser alternada a qualquer momento antes do fechamento."""

    command_repository: CommandRepositoryInterface

    async def execute(self, *, command_id: uuid.UUID, charged: bool) -> CommandResponse:
        command = await self.command_repository.get_by_id(command_id)
        if command is None:
            raise ResourceNotFoundException("Command", str(command_id))

        command.set_service_fee(charged)
        updated = await self.command_repository.save(command)
        return _to_response(updated)


@dataclass
class ListCommandsUseCase:
    command_repository: CommandRepositoryInterface

    async def execute(self, *, status: CommandStatus | None = None) -> list[CommandResponse]:
        commands = await self.command_repository.list_all(status=status)
        return [_to_response(c) for c in commands]
