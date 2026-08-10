"""Configurações de Runtime do Microsserviço de Estoque, Ficha Técnica e Baixa Automática."""

from __future__ import annotations

from restaurant_common.settings import (
    BaseAppSettings,
    DatabaseSettings,
    RabbitMQSettings,
)


class AppSettings(BaseAppSettings):
    """Configurações do `inventory-service`."""

    app_name: str = "Inventory & Recipes Microservice"
    port: int = 8006

    db: DatabaseSettings
    rabbitmq: RabbitMQSettings


settings = AppSettings()
