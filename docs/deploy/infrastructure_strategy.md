# 🚀 Estratégia de Deploy e Infraestrutura

> Complementa `ARCHITECTURE.md §5` e `ADR-005`. Fecha a lacuna apontada na auditoria de
> 2026-08-04 (link presente no índice do README sem conteúdo correspondente).

## Separação Dev vs Prod

O `docker-compose.yml` original (infra genérica única) foi substituído por
dois arquivos explícitos em `infra/docker/`, compondo um `docker-compose.base.yml`
comum via `include`/`extends` para não duplicar a definição dos 12 serviços:

| Arquivo | Uso | Postgres | Redis / RabbitMQ / Meilisearch |
|---|---|---|---|
| `docker-compose.dev.yml` | Desenvolvimento local | Container (`postgres:16-alpine`), volume local | Containers locais |
| `docker-compose.prod.yml` | Produção | **Externo/gerenciado** — nenhum container de banco sobe; serviços apontam `DB__HOST`/`DB__PORT` para a instância dedicada via `.env.prod` | Containers na mesma stack (decisão registrada nesta rodada: só o banco relacional é externo) |

Motivo: em produção o Postgres é uma instância dedicada e gerenciada
separadamente (backup, HA, monitoramento próprios) — nunca uma efêmera
dentro do Compose. Redis/RabbitMQ/Meilisearch permanecem containerizados por
simplicidade operacional nesta fase; podem migrar para serviços gerenciados
depois sem mudança de código (a URL é sempre injetada via `.env.prod`).

## Variáveis de ambiente por ambiente

- `.env.dev.example` → copiar para `.env.dev`, usado pelo `docker-compose.dev.yml`.
- `.env.prod.example` → copiar para `.env.prod`, usado pelo `docker-compose.prod.yml`.
  `DB__HOST`/`DB__PORT`/`DB__PASSWORD` do exemplo apontam para placeholders —
  nunca para uma instância real — o operador preenche na hora do deploy.
- Nenhum dos dois arquivos reais (`.env.dev`, `.env.prod`) é commitado
  (`.gitignore`); apenas os `.example` versionados.

## Build de imagens

Todo serviço em `services/<x>/Dockerfile` usa build multi-stage com `uv`
(`ADR-004`): estágio `builder` resolve dependências com `uv sync --frozen
--no-dev`, estágio final copia apenas `/app/.venv` + código para uma imagem
`python:3.12-slim-bookworm` — sem toolchain de build, < 150MB.

## CI/CD (GitHub Actions)

Pipeline por PR (`CONTRIBUTING.md`):
1. `ruff check .` + `ruff format --check .` em todo serviço/pacote alterado.
2. `mypy --strict` em todo serviço/pacote alterado.
3. `uv run pytest` (unit sempre; integration contra um Postgres de serviço
   do próprio runner do Actions).
4. `npm run lint && npm run type-check && npm run test` nos apps web afetados.
5. `flutter analyze && flutter test` nos apps mobile afetados.
6. Build da imagem Docker de cada serviço alterado (sem push em PR).

Merge em `main` dispara build + push de imagem versionada (tag = SHA curto)
e, em produção, `docker compose -f infra/docker/docker-compose.prod.yml pull
&& up -d` no host de destino.

## Observabilidade

- **Logs**: JSON estruturado no stdout de cada container (coletável por
  qualquer agregador — não fixamos um vendor).
- **Métricas**: Prometheus (`/metrics` por serviço, via `prometheus-fastapi-instrumentator`)
  + Grafana para dashboards.
- **Tracing distribuído**: OpenTelemetry Collector — cada requisição que
  atravessa múltiplos serviços (ex.: criação de pedido → Saga) carrega um
  `trace_id` correlacionável entre `order-service`, `inventory-service` e
  `kitchen-service`.
- **Health checks**: todo serviço expõe `GET /health`; usado tanto pelo
  `depends_on: condition: service_healthy` do Compose quanto pelas
  `livenessProbe`/`readinessProbe` do Kubernetes (`infra/k8s/`).
