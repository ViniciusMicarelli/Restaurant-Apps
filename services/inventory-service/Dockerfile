# syntax=docker/dockerfile:1.7
# Build multi-stage com `uv` (ADR-004).
#
# O contexto de build DEVE ser a raiz do repositório (não `services/inventory-service`),
# porque este serviço depende de pacotes do workspace uv (`packages/*`, ex:
# `restaurant-security`, `restaurant-database`). Ver
# `infra/docker/docker-compose.dev.yml` / `docker-compose.prod.yml`:
#   build:
#     context: ../..
#     dockerfile: services/inventory-service/Dockerfile

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

# 1) Manifests do workspace primeiro — camada cacheada, só invalida quando uma
#    dependência muda (não a cada alteração de código-fonte).
COPY pyproject.toml uv.lock /app/
COPY packages/ /app/packages/
COPY services/inventory-service/pyproject.toml /app/services/inventory-service/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package inventory-service

# 2) Código-fonte do serviço.
COPY services/inventory-service/ /app/services/inventory-service/

FROM python:3.14-slim-bookworm AS runtime
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app/services/inventory-service
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER appuser
EXPOSE 8006
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD python -c "import os,urllib.request,sys; p=os.environ.get('PORT','8006'); sys.exit(0 if urllib.request.urlopen(f'http://localhost:{p}/api/v1/inventory/health/check', timeout=3).status == 200 else 1)"
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8006}"]
