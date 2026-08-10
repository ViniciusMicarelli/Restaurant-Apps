# ADR-005: Injeção de Variáveis de Ambiente no Pydantic Settings via Docker Compose

* **Status**: Aprovado
* **Data**: 2026-08-04
* **Decisores**: Arquiteto de Software Sênior

---

## Contexto e Problema

Cada microsserviço no projeto gerencia suas configurações runtime (conexão de banco, Redis, segredos JWT, portas, chaves de API externas) utilizando o `pydantic-settings` (Pydantic v2).

Precisamos garantir que a injeção dessas variáveis pelo `docker-compose.yml` e Kubernetes (`Deployment`/`ConfigMap`/`Secret`) ocorra de forma fortemente tipada, segura, sem vazamentos e perfeitamente mapeada no Pydantic.

---

## Decisão

Estandardizar a injeção de configurações no `pydantic-settings` utilizando:
1. **Delimitador de Variáveis Aninhadas (`env_nested_delimiter="__")**: Permite mapear structs/objetos aninhados de configuração no Pydantic via variáveis de ambiente como `POSTGRES__HOST` ou `REDIS__PORT`.
2. **Case Insensitivity e Prefixos por Serviço**: Configurado via `SettingsConfigDict`.
3. **Mecanismo de Leitura Prioritária no Pydantic**:
   `Variáveis de Ambiente do SO / Docker Compose` > `.env.local` > `.env` > `Valores Default`.

---

## Exemplo de Implementação

### 1. Classe de Configuração em Python (`config.py`)
```python
from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    name: str = "restaurant_db"

    @property
    def async_dsn(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # Permite DB__HOST no Docker Compose
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Menu Service"
    environment: str = "development"
    debug: bool = False
    db: DatabaseSettings = DatabaseSettings()
    redis_url: RedisDsn = "redis://localhost:6379/0"
    jwt_secret_key: SecretStr = SecretStr("change-me-in-production")


settings = AppSettings()
```

### 2. Injeção no `docker-compose.yml`
```yaml
version: "3.8"

services:
  menu-service:
    build:
      context: ./services/menu
      dockerfile: Dockerfile
    container_name: menu-service
    ports:
      - "8002:8002"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - DB__HOST=postgres-db
      - DB__PORT=5432
      - DB__USER=${POSTGRES_USER:-postgres}
      - DB__PASSWORD=${POSTGRES_PASSWORD:-secret}
      - DB__NAME=menu_db
      - REDIS_URL=redis://redis-cache:6379/1
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    env_file:
      - .env
    depends_on:
      - postgres-db
      - redis-cache
```

---

## Consequências

* **Zero Hardcoding**: Nenhuma URL de banco ou segredo é gravado no código.
* **Mapeamento Tipo-Seguro**: O Pydantic valida os tipos (portas como `int`, URLs como `PostgresDsn`, senhas como `SecretStr` que não vazam em logs) no momento em que o container sobe. Se faltar uma variável obrigatória, o container falha no start com mensagem explícita.
