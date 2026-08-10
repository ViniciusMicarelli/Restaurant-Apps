"""Testes do gerador de UUIDv7 (RFC 9562)."""

import time
import uuid

from restaurant_core.ids import generate_uuid7


def test_generate_uuid7_returns_valid_uuid_with_correct_version_and_variant() -> None:
    """O UUID gerado deve declarar versão 7 e variante RFC 4122 corretamente."""
    generated = generate_uuid7()

    assert isinstance(generated, uuid.UUID)
    assert generated.version == 7
    assert generated.variant == uuid.RFC_4122


def test_generate_uuid7_is_monotonically_sortable_across_calls() -> None:
    """UUIDs gerados em sequência devem ser ordenáveis cronologicamente (binário/lexicográfico)."""
    first = generate_uuid7()
    time.sleep(0.002)
    second = generate_uuid7()

    assert first.bytes < second.bytes
    assert str(first) < str(second)


def test_generate_uuid7_produces_unique_values() -> None:
    """Chamadas sucessivas nunca devem colidir, mesmo dentro do mesmo milissegundo."""
    generated_ids = {generate_uuid7() for _ in range(1000)}

    assert len(generated_ids) == 1000


def test_generate_uuid7_embeds_current_unix_timestamp_ms() -> None:
    """Os 48 bits mais significativos devem corresponder ao timestamp Unix em ms no momento da geração."""
    before_ms = int(time.time() * 1000)
    generated = generate_uuid7()
    after_ms = int(time.time() * 1000)

    embedded_ts_ms = int.from_bytes(generated.bytes[0:6], byteorder="big")

    assert before_ms <= embedded_ts_ms <= after_ms
