"""Configurações de Runtime do Microsserviço de Cozinha e KDS (Kitchen Display System)."""

from __future__ import annotations

from restaurant_common.settings import (
    BaseAppSettings,
    DatabaseSettings,
    RabbitMQSettings,
)


class AppSettings(BaseAppSettings):
    """Configurações do `kitchen-service`."""

    app_name: str = "Kitchen & KDS Microservice"
    port: int = 8004

    db: DatabaseSettings
    rabbitmq: RabbitMQSettings


settings = AppSettings()
