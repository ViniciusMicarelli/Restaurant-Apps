# ADR-004: Gerenciamento de Pacotes Python com `uv`

* **Status**: Aprovado
* **Data**: 2026-08-04
* **Decisores**: Arquiteto de Software Sênior

---

## Contexto e Problema

Em um projeto de microsserviços com dezenas de microsserviços e workers Python/FastAPI, o gerenciamento de dependências tradicional com `pip` ou `poetry` pode se tornar lento em builds de Docker e CI/CD, além de consumir recursos expressivos na resolução de grafos de dependências complexos.

---

## Decisão

Decidimos adotar o **`uv`** (desenvolvido em Rust pela Astral) como o gerenciador de pacotes, ambientes virtuais (`.venv`) e dependências padrão em todo o ecossistema Python da plataforma.

---

## Mecanismo de Utilização

1. **Configuração dos Serviços**: Cada microsserviço em `services/<service_name>` conterá seu próprio `pyproject.toml` e arquivo de trava determinístico `uv.lock`.
2. **Build de Docker Multi-Stage de Altíssima Performance**:
   ```dockerfile
   # Exemplo de Dockerfile otimizado com uv
   FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
   ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
   WORKDIR /app
   RUN --mount=type=cache,target=/root/.cache/uv \
       --mount=type=bind,source=uv.lock,target=uv.lock \
       --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
       uv sync --frozen --no-install-project --no-dev

   ADD . /app
   RUN --mount=type=cache,target=/root/.cache/uv \
       uv sync --frozen --no-dev

   FROM python:3.12-slim-bookworm
   COPY --from=builder /app /app
   ENV PATH="/app/.venv/bin:$PATH"
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Vantagens**:
   * Instalação e resolução de dependências até **10x a 100x mais rápida** que `pip`/`poetry`.
   * Reprodutibilidade exata de builds via `uv.lock`.
   * Suporte nativo a Workspaces para o monorepo (`uv workspace`).
