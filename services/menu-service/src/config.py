"""Configurações de Runtime do Microsserviço de Cardápio e Busca FTS."""

from __future__ import annotations

from pydantic import SecretStr
from restaurant_common.settings import BaseAppSettings, DatabaseSettings, RedisSettings


class AppSettings(BaseAppSettings):
    """Configurações do `menu-service`."""

    app_name: str = "Menu & Catalog Microservice"
    port: int = 8002

    db: DatabaseSettings
    redis: RedisSettings
    meilisearch_url: str
    meilisearch_master_key: SecretStr
    # Rotas públicas do cardápio digital (docs/SECURITY.md §2.7 —
    # "endpoints de API pública: máx 100 req/min por tenant").
    public_rate_limit_max_requests: int = 100
    public_rate_limit_window_seconds: int = 60


settings = AppSettings()
