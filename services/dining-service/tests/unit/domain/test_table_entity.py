"""Testes da entidade de domínio `Table` (máquina de estados)."""

import uuid

import pytest
from src.domain.entities.table import Table, TableStatus


def _make_table(status: TableStatus = TableStatus.AVAILABLE) -> Table:
    return Table(id=uuid.uuid4(), tenant_id=uuid.uuid4(), number=1, capacity=4, status=status)


def test_available_table_can_transition_to_occupied() -> None:
    table = _make_table(TableStatus.AVAILABLE)
    table.transition_to(TableStatus.OCCUPIED)
    assert table.status == TableStatus.OCCUPIED


def test_occupied_table_can_transition_to_waiting_cleaning() -> None:
    table = _make_table(TableStatus.OCCUPIED)
    table.transition_to(TableStatus.WAITING_CLEANING)
    assert table.status == TableStatus.WAITING_CLEANING


def test_waiting_cleaning_table_can_transition_back_to_available() -> None:
    table = _make_table(TableStatus.WAITING_CLEANING)
    table.transition_to(TableStatus.AVAILABLE)
    assert table.status == TableStatus.AVAILABLE


def test_occupied_table_cannot_transition_directly_to_available() -> None:
    table = _make_table(TableStatus.OCCUPIED)
    with pytest.raises(ValueError, match="Transição inválida"):
        table.transition_to(TableStatus.AVAILABLE)


def test_reserved_table_can_transition_to_occupied_or_available() -> None:
    table = _make_table(TableStatus.RESERVED)
    table.transition_to(TableStatus.OCCUPIED)
    assert table.status == TableStatus.OCCUPIED
