"""Configurações de Runtime do Microsserviço de Notificações."""

from __future__ import annotations

from restaurant_common.settings import BaseAppSettings, DatabaseSettings, RabbitMQSettings


class AppSettings(BaseAppSettings):
    """Configurações do `notification-service`."""

    app_name: str = "Notifications Microservice"
    port: int = 8010

    db: DatabaseSettings
    rabbitmq: RabbitMQSettings


settings = AppSettings()
