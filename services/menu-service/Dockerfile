# syntax=docker/dockerfile:1.7
# Build multi-stage com `uv` (ADR-004).
#
# O contexto de build DEVE ser a raiz do repositório (não `services/menu-service`),
# porque este serviço depende de pacotes do workspace uv (`packages/*`, ex:
# `restaurant-security`, `restaurant-database`). Ver
# `infra/docker/docker-compose.dev.yml` / `docker-compose.prod.yml`:
#   build:
#     context: ../..
#     dockerfile: services/menu-service/Dockerfile

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

# 1) Manifests do workspace primeiro — camada cacheada, só invalida quando uma
#    dependência muda (não a cada alteração de código-fonte).
COPY pyproject.toml uv.lock /app/
COPY packages/ /app/packages/
COPY services/menu-service/pyproject.toml /app/services/menu-service/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package menu-service

# 2) Código-fonte do serviço.
COPY services/menu-service/ /app/services/menu-service/

FROM python:3.12-slim-bookworm AS runtime
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app/services/menu-service
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER appuser
EXPOSE 8002
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8002/api/v1/menu/health/check', timeout=3).status == 200 else 1)"
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
