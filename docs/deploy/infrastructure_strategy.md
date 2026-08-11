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

## CI/CD (GitHub Actions + Railway)

Implementado em `.github/workflows/ci.yml` (2026-08-10) — roda em PR
contra `staging`/`main` e em push direto nas duas:
1. `ruff check .` + `ruff format --check .` (workspace inteiro, um job só).
2. `mypy --strict` por serviço/pacote/worker (matriz — 12 microsserviços +
   `workers` + 5 pacotes compartilhados).
3. `uv run pytest` por serviço/pacote/worker — testes de integração usam
   SQLite em memória (`conftest.py` de cada serviço), não depende de um
   Postgres real no runner.
4. `npm run build && npm test` nos 2 web apps (`build` já roda `tsc`).
5. `flutter analyze && flutter test` nos 2 apps mobile.
6. Build de imagem Docker de cada serviço/app (sem push) — valida que
   todo `Dockerfile` continua correto.

Dependências mantidas via Dependabot (`.github/dependabot.yml` — `uv`,
`npm`×3, `pub`×2, `docker`×15, `github-actions`; tudo mirando `staging`,
passa pelo mesmo CI antes de chegar em `main`).

**Deploy**: Railway (branch `staging` → environment de staging, `main` →
produção — redeploy automático a cada push, a Railway já observa o
repositório). Não é mais `docker compose pull && up` manual num host —
ver `docs/deploy/railway_setup.md` pro guia completo (17 serviços
deployáveis, cada um com seu `railway.json` ao lado do `Dockerfile`).
Todo `Dockerfile` de serviço/app lê a porta via `$PORT` dinâmico (ajuste
necessário pra Railway — antes hardcodava a porta de dev).

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
