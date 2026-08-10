"""Configurações de Runtime do Microsserviço Motor de Pedidos e Orquestrador de Sagas."""

from __future__ import annotations

from restaurant_common.settings import (
    BaseAppSettings,
    DatabaseSettings,
    RabbitMQSettings,
    RedisSettings,
)


class AppSettings(BaseAppSettings):
    """Configurações do `order-service`."""

    app_name: str = "Orders & Saga Microservice"
    port: int = 8005

    db: DatabaseSettings
    redis: RedisSettings
    rabbitmq: RabbitMQSettings


settings = AppSettings()
