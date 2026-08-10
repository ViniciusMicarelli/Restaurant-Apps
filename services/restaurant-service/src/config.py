"""Configurações de Runtime do Microsserviço de Restaurantes e Branding."""

from __future__ import annotations

from restaurant_common.settings import BaseAppSettings, DatabaseSettings, RedisSettings


class AppSettings(BaseAppSettings):
    """Configurações do `restaurant-service`."""

    app_name: str = "Restaurant & Branding Microservice"
    port: int = 8001

    db: DatabaseSettings
    redis: RedisSettings
    # Rotas públicas (bootstrap de tenant + consultas por slug/ID —
    # docs/SECURITY.md §2.7, "endpoints de API pública: máx 100 req/min").
    public_rate_limit_max_requests: int = 100
    public_rate_limit_window_seconds: int = 60
    # Só `true` em produção (setado explicitamente no docker-compose.prod.yml,
    # mesmo raciocínio já documentado no `auth-service` pro rate limit de
    # login) — lá o `restaurant-service` só é alcançável via o Nginx do API
    # Gateway, então o último IP de `X-Forwarded-For` é sempre o real.
    trust_proxy_headers: bool = False


settings = AppSettings()
