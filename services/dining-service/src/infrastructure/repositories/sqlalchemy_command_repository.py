"""Implementação concreta de `CommandRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.command import Command, CommandStatus
from src.infrastructure.models.command_model import CommandModel


def _to_entity(model: CommandModel) -> Command:
    return Command(
        id=model.id,
        tenant_id=model.tenant_id,
        table_id=model.table_id,
        customer_name=model.customer_name,
        customer_cpf=model.customer_cpf,
        waiter_id=model.waiter_id,
        status=model.status,
        opened_at=model.opened_at,
        closed_at=model.closed_at,
        service_fee_charged=model.service_fee_charged,
    )


class SQLAlchemyCommandRepository(SQLAlchemyRepository[CommandModel]):
    model = CommandModel

    async def get_by_id(self, command_id: uuid.UUID) -> Command | None:
        model = await super().get_model_by_id(command_id)
        return _to_entity(model) if model is not None else None

    async def get_open_command_for_table(self, table_id: uuid.UUID) -> Command | None:
        stmt = select(CommandModel).where(
            CommandModel.tenant_id == self._tenant_id,
            CommandModel.table_id == table_id,
            CommandModel.status == CommandStatus.OPEN,
            CommandModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_all(self, *, status: CommandStatus | None = None) -> list[Command]:
        stmt = (
            select(CommandModel)
            .where(CommandModel.tenant_id == self._tenant_id, CommandModel.deleted_at.is_(None))
            .order_by(CommandModel.opened_at.desc())
            .limit(1000)
        )
        if status is not None:
            stmt = stmt.where(CommandModel.status == status)
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def add(self, command: Command) -> Command:
        model = CommandModel(
            id=command.id,
            tenant_id=command.tenant_id,
            table_id=command.table_id,
            customer_name=command.customer_name,
            customer_cpf=command.customer_cpf,
            waiter_id=command.waiter_id,
            status=command.status,
            opened_at=command.opened_at,
            closed_at=command.closed_at,
            service_fee_charged=command.service_fee_charged,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, command: Command) -> Command:
        model = await self._session.get(CommandModel, command.id)
        if model is None:
            msg = f"Comanda '{command.id}' não encontrada para atualização."
            raise LookupError(msg)
        model.status = command.status
        model.closed_at = command.closed_at
        model.service_fee_charged = command.service_fee_charged
        saved = await super().save_model(model)
        return _to_entity(saved)
