"""Configurações de Runtime dos Workers assíncronos (Dramatiq/Redis — ADR-002).

Lê estritamente de variáveis de ambiente/`.env` — nenhuma secret hardcoded
(docs/SECURITY.md). O broker Redis dos workers é isolado (`WORKERS_REDIS_DB`)
dos DBs Redis de cache/idempotência de cada microsserviço.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings
from restaurant_common.settings import RabbitMQSettings, RedisSettings, build_settings_config


class WorkerSettings(BaseSettings):
    """Configurações dos workers, lidas via `.env` centralizado."""

    model_config = build_settings_config()

    environment: str
    redis: RedisSettings
    rabbitmq: RabbitMQSettings


settings = WorkerSettings()
