"""Testes da entidade de domínio `Command` (comanda)."""

import uuid

import pytest
from src.domain.entities.command import Command, CommandStatus


def _make_command() -> Command:
    return Command(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        table_id=uuid.uuid4(),
        customer_name="Lucas",
        waiter_id=uuid.uuid4(),
    )


def test_new_command_starts_open_with_opened_at_set() -> None:
    command = _make_command()
    assert command.status == CommandStatus.OPEN
    assert command.opened_at is not None
    assert command.closed_at is None


def test_close_sets_status_and_closed_at() -> None:
    command = _make_command()
    command.close()
    assert command.status == CommandStatus.CLOSED
    assert command.closed_at is not None


def test_close_an_already_closed_command_raises() -> None:
    command = _make_command()
    command.close()
    with pytest.raises(ValueError, match="já está fechada"):
        command.close()
