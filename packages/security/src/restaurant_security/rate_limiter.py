"""Rate limiting hand-rolled sobre Redis (docs/SECURITY.md §2.7) — janela
fixa (`INCR`+`EXPIRE`), escolhido sobre uma lib nova (`slowapi`/`limits`)
porque o algoritmo cabe em poucas linhas e o Redis já é dependência de
praticamente todo serviço da plataforma.

Promovido de `auth-service` (onde nasceu, 2026-08-10, protegendo `/login`)
pra cá quando o mesmo padrão passou a ser necessário em mais serviços
(`dining`/`menu`/`payment`/`restaurant`, pra proteger as rotas públicas do
autoatendimento — mesma data) — evita duplicar a mesma implementação até 5
vezes em vez de compartilhar via pacote, do mesmo jeito que
`TenantContextMiddleware`/JWT já são compartilhados.
"""

from __future__ import annotations

from redis.asyncio import Redis
from starlette.requests import Request

from restaurant_security.tenant_context import get_current_tenant_id_or_none


class RedisRateLimiter:
    """Janela fixa: o contador expira `window_seconds` depois da PRIMEIRA
    tentativa da janela (não desliza a cada `hit`) — simples e suficiente
    pra throttle de força bruta/abuso, mesma trade-off que o `limit_req`
    do Nginx de produção já faz.

    `key_prefix` é só uma conveniência de namespacing/depuração (inspecionar
    chaves no Redis) — cada serviço já tem seu próprio banco Redis isolado
    (`REDIS__DB` distinto por serviço, ver `.env.dev`/`.env.prod`), então
    colisão entre serviços não é possível mesmo sem prefixo.
    """

    def __init__(self, redis_client: Redis, key_prefix: str = "rate-limit:") -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix

    async def hit(self, key: str, *, max_attempts: int, window_seconds: int) -> bool:
        """Registra uma tentativa sob `key` e retorna `True` se ainda
        dentro do limite, `False` se `key` já excedeu `max_attempts`
        tentativas na janela corrente."""
        redis_key = f"{self._key_prefix}{key}"
        count = await self._redis.incr(redis_key)
        if count == 1:
            await self._redis.expire(redis_key, window_seconds)
        return count <= max_attempts


class InMemoryRateLimiter:
    """Implementação em memória — usada em testes unitários/integração,
    sem depender de Redis real (mesmo papel de `InMemoryTokenBlacklist`)."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    async def hit(self, key: str, *, max_attempts: int, window_seconds: int) -> bool:
        del window_seconds  # sem expiração real nesta implementação
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key] <= max_attempts

    def reset(self) -> None:
        self._counts.clear()


def resolve_rate_limit_key(request: Request, *, trust_proxy_headers: bool = False) -> str:
    """Chave de rate limiting pra rotas públicas (docs/SECURITY.md §2.7 —
    "100 req/min por tenant"): usa o `tenant_id` já resolvido pelo
    `TenantContextMiddleware` (via `X-Tenant-Id` — estas rotas nunca exigem
    JWT) quando disponível. Cai pra IP do cliente quando não há tenant
    ainda — só o caso do bootstrap de um restaurante novo
    (`POST /restaurants`) e das consultas públicas por slug/ID que o
    precedem, onde não existe tenant pra chavear (mesma granularidade que
    a zona `api_general` do Nginx já usa: só IP).

    `trust_proxy_headers` segue o mesmo raciocínio já documentado em
    `auth-service` pro rate limit de login: só usar o último valor de
    `X-Forwarded-For` (o que o Nginx do próprio Gateway garante não ter
    sido forjado) quando o serviço está atrás dele de verdade (produção).
    """
    tenant_id = get_current_tenant_id_or_none()
    if tenant_id is not None:
        return f"tenant:{tenant_id}"

    if trust_proxy_headers:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[-1].strip()}"

    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"
