"""Configurações de Runtime do Microsserviço de Marketing & Fidelidade."""

from __future__ import annotations

from restaurant_common.settings import BaseAppSettings, DatabaseSettings


class AppSettings(BaseAppSettings):
    """Configurações do `marketing-service`."""

    app_name: str = "Marketing & Loyalty Microservice"
    port: int = 8009

    db: DatabaseSettings


settings = AppSettings()
