"""Fakes em memória das interfaces de `application/interfaces` — usados pelos testes unitários."""

from __future__ import annotations

import uuid

from src.domain.entities.command import Command, CommandStatus
from src.domain.entities.queue_entry import QueueEntry, QueueStatus
from src.domain.entities.table import Table


class FakeTableStore:
    def __init__(self, tables: list[Table] | None = None) -> None:
        self._tables: dict[uuid.UUID, Table] = {t.id: t for t in (tables or [])}

    async def get_by_id(self, table_id: uuid.UUID) -> Table | None:
        return self._tables.get(table_id)

    async def get_by_number(self, number: int) -> Table | None:
        return next((t for t in self._tables.values() if t.number == number), None)

    async def list_all(self) -> list[Table]:
        return list(self._tables.values())

    async def add(self, table: Table) -> Table:
        self._tables[table.id] = table
        return table

    async def save(self, table: Table) -> Table:
        self._tables[table.id] = table
        return table


class FakeCommandStore:
    def __init__(self, commands: list[Command] | None = None) -> None:
        self._commands: dict[uuid.UUID, Command] = {c.id: c for c in (commands or [])}

    async def get_by_id(self, command_id: uuid.UUID) -> Command | None:
        return self._commands.get(command_id)

    async def get_open_command_for_table(self, table_id: uuid.UUID) -> Command | None:
        return next(
            (
                c
                for c in self._commands.values()
                if c.table_id == table_id and c.status == CommandStatus.OPEN
            ),
            None,
        )

    async def list_all(self, *, status: CommandStatus | None = None) -> list[Command]:
        commands = list(self._commands.values())
        if status is not None:
            commands = [c for c in commands if c.status == status]
        return commands

    async def add(self, command: Command) -> Command:
        self._commands[command.id] = command
        return command

    async def save(self, command: Command) -> Command:
        self._commands[command.id] = command
        return command


class FakeQueueStore:
    def __init__(self, entries: list[QueueEntry] | None = None) -> None:
        self._entries: dict[uuid.UUID, QueueEntry] = {e.id: e for e in (entries or [])}

    async def get_by_id(self, entry_id: uuid.UUID) -> QueueEntry | None:
        return self._entries.get(entry_id)

    async def list_waiting(self) -> list[QueueEntry]:
        waiting = [e for e in self._entries.values() if e.status == QueueStatus.WAITING]
        return sorted(waiting, key=lambda e: e.created_at)

    async def add(self, entry: QueueEntry) -> QueueEntry:
        self._entries[entry.id] = entry
        return entry

    async def save(self, entry: QueueEntry) -> QueueEntry:
        self._entries[entry.id] = entry
        return entry
