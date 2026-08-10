"""Testes do tipo de coluna `GUID` agnóstico de dialeto SQL."""

import uuid

from restaurant_database.guid import GUID
from sqlalchemy.dialects import postgresql, sqlite

_GUID = GUID()
_PG_DIALECT = postgresql.dialect()
_SQLITE_DIALECT = sqlite.dialect()


def test_bind_and_result_round_trip_on_postgresql_dialect() -> None:
    original = uuid.uuid4()

    bound = _GUID.process_bind_param(original, _PG_DIALECT)
    restored = _GUID.process_result_value(bound, _PG_DIALECT)

    assert restored == original


def test_bind_and_result_round_trip_on_sqlite_dialect() -> None:
    original = uuid.uuid4()

    bound = _GUID.process_bind_param(original, _SQLITE_DIALECT)
    assert bound == original.hex

    restored = _GUID.process_result_value(bound, _SQLITE_DIALECT)
    assert restored == original


def test_process_bind_param_accepts_none() -> None:
    assert _GUID.process_bind_param(None, _SQLITE_DIALECT) is None


def test_process_result_value_accepts_none() -> None:
    assert _GUID.process_result_value(None, _SQLITE_DIALECT) is None


def test_process_bind_param_accepts_string_uuid() -> None:
    original = uuid.uuid4()

    bound = _GUID.process_bind_param(str(original), _SQLITE_DIALECT)

    assert bound == original.hex
