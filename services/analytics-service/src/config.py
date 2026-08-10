"""Configurações de Runtime do Microsserviço de Analytics & Auditoria."""

from __future__ import annotations

from restaurant_common.settings import BaseAppSettings, DatabaseSettings, RabbitMQSettings


class AppSettings(BaseAppSettings):
    """Configurações do `analytics-service`."""

    app_name: str = "Analytics & Audit Microservice"
    port: int = 8011

    db: DatabaseSettings
    rabbitmq: RabbitMQSettings


settings = AppSettings()
