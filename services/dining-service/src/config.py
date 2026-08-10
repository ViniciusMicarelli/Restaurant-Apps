"""Configurações de Runtime do Microsserviço de Salão, Mesas e Comandas."""

from __future__ import annotations

from restaurant_common.settings import BaseAppSettings, DatabaseSettings, RedisSettings


class AppSettings(BaseAppSettings):
    """Configurações do `dining-service`."""

    app_name: str = "Dining & Tables Microservice"
    port: int = 8003

    db: DatabaseSettings
    redis: RedisSettings
    # Rotas públicas do autoatendimento do cliente (docs/SECURITY.md §2.7 —
    # "endpoints de API pública: máx 100 req/min por tenant").
    public_rate_limit_max_requests: int = 100
    public_rate_limit_window_seconds: int = 60


settings = AppSettings()
