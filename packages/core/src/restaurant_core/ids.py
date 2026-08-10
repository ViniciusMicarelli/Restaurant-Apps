"""Geração de identificadores UUIDv7 (RFC 9562) — ordenáveis no tempo.

UUIDv7 combina um timestamp Unix em milissegundos (48 bits, big-endian) com
bits aleatórios, permitindo que os IDs sejam monotonicamente crescentes por
ordem de criação (índices B-Tree mais eficientes que UUIDv4 puro) sem expor
informação sequencial previsível como um ID numérico incremental.

Layout dos 128 bits (RFC 9562 §5.7):
    - 48 bits: unix_ts_ms (timestamp Unix em milissegundos, big-endian)
    - 4 bits:  ver (versão fixa 0b0111)
    - 12 bits: rand_a (aleatório)
    - 2 bits:  var (variante fixa 0b10)
    - 62 bits: rand_b (aleatório)
"""

from __future__ import annotations

import os
import time
import uuid


def generate_uuid7() -> uuid.UUID:
    """Gera um UUIDv7 compatível com a RFC 9562.

    Returns:
        Um `uuid.UUID` cuja ordenação lexicográfica/binária acompanha a
        ordem cronológica de criação.
    """
    unix_ts_ms = int(time.time() * 1000)
    ts_bytes = unix_ts_ms.to_bytes(6, byteorder="big")
    rand_bytes = bytearray(os.urandom(10))

    # Byte 6: 4 bits altos = versão (0111), 4 bits baixos = topo do rand_a.
    rand_bytes[0] = (rand_bytes[0] & 0x0F) | 0x70
    # Byte 8: 2 bits altos = variante (10), 6 bits baixos = topo do rand_b.
    rand_bytes[2] = (rand_bytes[2] & 0x3F) | 0x80

    return uuid.UUID(bytes=bytes(ts_bytes + rand_bytes))
