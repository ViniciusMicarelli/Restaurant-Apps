"""Blocos de configuração reutilizáveis via `pydantic-settings` (ADR-005).

Cada microsserviço compõe seu próprio `AppSettings` a partir destes blocos,
evitando duplicar a definição de `DatabaseSettings`/`RedisSettings` doze
vezes. Exemplo de uso em `services/<x>/src/config.py`:

    class AppSettings(BaseAppSettings):
        app_name: str = "Menu Service"
        port: int = 8002
        db: DatabaseSettings
        redis: RedisSettings

    settings = AppSettings()
"""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def build_settings_config(env_file: str = "../../.env.dev") -> SettingsConfigDict:
    """Configuração padrão do `pydantic-settings` usada por todos os serviços.

    `env_file` é apenas uma conveniência para rodar um serviço fora do Docker
    (ex: `uv run uvicorn src.main:app`); dentro de qualquer container (dev ou
    prod) as variáveis já chegam via `environment`/`env_file` do próprio
    Docker Compose, que têm prioridade e tornam este arquivo irrelevante
    (`.env.dev`/`.env.prod` nunca são copiados para a imagem).

    Prioridade de leitura (ADR-005): variáveis de ambiente do SO/Docker Compose
    > `.env.local` > `.env` > valores default no código.
    """
    return SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    """Configurações do PostgreSQL isolado (Database-per-Service) de um microsserviço."""

    model_config = build_settings_config()

    host: str
    port: int
    user: str
    password: SecretStr
    name: str

    @property
    def async_dsn(self) -> str:
        """DSN assíncrono para o SQLAlchemy 2.0 Async Engine via `asyncpg`."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class RedisSettings(BaseSettings):
    """Configurações do Redis (cache, locks, filas de idempotência) de um microsserviço."""

    model_config = build_settings_config()

    host: str
    port: int
    db: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class RabbitMQSettings(BaseSettings):
    """Configurações do RabbitMQ (barramento de eventos de domínio da Saga)."""

    model_config = build_settings_config()

    host: str
    port: int
    user: str
    password: SecretStr

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/"


class BaseAppSettings(BaseSettings):
    """Campos comuns a todo microsserviço: ambiente, debug, porta e segredo JWT.

    A verificação do JWT é feita localmente por cada serviço (o segredo é
    compartilhado via `.env`), evitando uma chamada de rede ao `auth-service`
    a cada requisição só para validar o token.
    """

    model_config = build_settings_config()

    environment: str
    debug: bool
    port: int
    jwt_secret_key: SecretStr

    # Lista explícita de origens permitidas por CORS. `["*"]` é o default de
    # conveniência para dev; `allow_origins=["*"]` é proibido em produção
    # (docs/SECURITY.md) — `.env.prod` deve sempre definir `CORS_ALLOWED_ORIGINS`
    # como um array JSON com os domínios reais dos frontends.
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
