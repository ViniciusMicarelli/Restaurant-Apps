"""Configurações de Runtime do Microsserviço de Delivery & Retirada."""

from __future__ import annotations

from restaurant_common.settings import BaseAppSettings, DatabaseSettings


class AppSettings(BaseAppSettings):
    """Configurações do `delivery-service`."""

    app_name: str = "Delivery & Takeout Microservice"
    port: int = 8008

    db: DatabaseSettings


settings = AppSettings()
