# syntax=docker/dockerfile:1.7
# Build multi-stage com `uv` (ADR-004).
#
# O contexto de build DEVE ser a raiz do repositório (não `services/order-service`),
# porque este serviço depende de pacotes do workspace uv (`packages/*`, ex:
# `restaurant-security`, `restaurant-database`). Ver
# `infra/docker/docker-compose.dev.yml` / `docker-compose.prod.yml`:
#   build:
#     context: ../..
#     dockerfile: services/order-service/Dockerfile

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

# 1) Manifests do workspace primeiro — camada cacheada, só invalida quando uma
#    dependência muda (não a cada alteração de código-fonte).
COPY pyproject.toml uv.lock /app/
COPY packages/ /app/packages/
COPY services/order-service/pyproject.toml /app/services/order-service/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package order-service

# 2) Código-fonte do serviço.
COPY services/order-service/ /app/services/order-service/

FROM python:3.14-slim-bookworm AS runtime
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app/services/order-service
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER appuser
EXPOSE 8005
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD python -c "import os,urllib.request,sys; p=os.environ.get('PORT','8005'); sys.exit(0 if urllib.request.urlopen(f'http://localhost:{p}/api/v1/orders/health/check', timeout=3).status == 200 else 1)"
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8005}"]
