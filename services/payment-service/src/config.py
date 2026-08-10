"""Configurações de Runtime do Microsserviço de Pagamentos e Caixa Operacional."""

from __future__ import annotations

from restaurant_common.settings import (
    BaseAppSettings,
    DatabaseSettings,
    RedisSettings,
)


class AppSettings(BaseAppSettings):
    """Configurações do `payment-service`."""

    app_name: str = "Payments & Cashier Microservice"
    port: int = 8007

    db: DatabaseSettings
    redis: RedisSettings
    # Chamadas REST síncronas a outros microsserviços (docs/ai/architecture.md
    # #1 permite explicitamente) — usadas pra computar o valor autoritativo
    # de uma comanda no servidor, nunca confiando no que o cliente mandar
    # (revisão de segurança, docs/logs/2026-08-10.md): dining-service confirma
    # a secret da mesa + a comanda aberta; order-service dá o total real dos
    # pedidos; restaurant-service dá a taxa de serviço configurada.
    dining_service_url: str = "http://dining-service:8003"
    order_service_url: str = "http://order-service:8005"
    restaurant_service_url: str = "http://restaurant-service:8001"
    # Rota pública do autoatendimento (docs/SECURITY.md §2.7 — "endpoints
    # de API pública: máx 100 req/min por tenant").
    public_rate_limit_max_requests: int = 100
    public_rate_limit_window_seconds: int = 60


settings = AppSettings()
