"""Configuração do Broker Dramatiq (Redis — ADR-002).

Importado (por efeito colateral) antes de qualquer módulo que declare um
`@dramatiq.actor`, garantindo que o broker global já esteja configurado no
momento do registro do actor.
"""

from __future__ import annotations

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from src.config import settings

redis_broker = RedisBroker(  # type: ignore[no-untyped-call]
    url=settings.redis.url
)  # dramatiq não publica stubs de tipos (biblioteca sem `py.typed`)
dramatiq.set_broker(redis_broker)
