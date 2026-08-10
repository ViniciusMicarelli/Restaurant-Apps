"""Configurações de Runtime do Microsserviço de Autenticação.

Lê estritamente do `.env` centralizado (via Docker Compose em dev/prod) sem
fallbacks hardcoded — variável obrigatória ausente derruba o container no
boot com uma mensagem de erro explícita (ADR-005).
"""

from __future__ import annotations

from restaurant_common.settings import BaseAppSettings, DatabaseSettings, RedisSettings


class AppSettings(BaseAppSettings):
    """Configurações do `auth-service`."""

    app_name: str = "Auth & Identity Microservice"
    port: int = 8000

    db: DatabaseSettings
    redis: RedisSettings
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # Força bruta em /login e /login-pin (docs/SECURITY.md §2.7).
    login_rate_limit_max_attempts: int = 5
    login_rate_limit_window_seconds: int = 60
    # Só `true` em produção (setado explicitamente no docker-compose.prod.yml)
    # — lá o auth-service só é alcançável através do Nginx do API Gateway
    # (nunca publicado direto, ver docker-compose.prod.yml), então o último
    # IP da cadeia X-Forwarded-For é sempre o que o Nginx viu de verdade.
    # Em dev (sem proxy na frente), confiar nesse header seria só um jeito
    # fácil de burlar o rate limiter (default False é o seguro).
    trust_proxy_headers: bool = False


settings = AppSettings()
