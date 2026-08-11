# syntax=docker/dockerfile:1.7
# Build multi-stage com `uv` (ADR-004).
#
# O contexto de build DEVE ser a raiz do repositório (não `workers/`), porque
# este pacote depende de outros membros do workspace uv (`packages/*`, ex:
# `restaurant-common`, `restaurant-events`). Ver
# `infra/docker/docker-compose.dev.yml` / `docker-compose.prod.yml`:
#   build:
#     context: ../..
#     dockerfile: workers/Dockerfile
#
# Três processos rodam desta mesma imagem, com `command:` diferente por
# container no compose (worker Dramatiq, bridge de notificações, agendador) —
# ver ADR-002.

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

# 1) Manifests do workspace primeiro — camada cacheada, só invalida quando uma
#    dependência muda (não a cada alteração de código-fonte).
COPY pyproject.toml uv.lock /app/
COPY packages/ /app/packages/
COPY workers/pyproject.toml /app/workers/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package workers

# 2) Código-fonte dos workers.
COPY workers/ /app/workers/

FROM python:3.14-slim-bookworm AS runtime
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app/workers
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER appuser
CMD ["dramatiq", "src.async_tasks", "--processes", "1", "--threads", "4"]
