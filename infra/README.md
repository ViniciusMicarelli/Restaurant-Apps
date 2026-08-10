# Infra — Restaurant Apps Platform

## Docker Compose: dev vs prod

| | `docker/docker-compose.dev.yml` | `docker/docker-compose.prod.yml` |
|---|---|---|
| Postgres | Container local (`postgres:16-alpine`), cria 1 banco por serviço via `scripts/create-service-databases.sh` | **Nenhum** — `DB__HOST`/`DB__PORT` em `.env.prod` apontam para uma instância dedicada/gerenciada externa |
| Redis / RabbitMQ / Meilisearch | Containers locais | Containers na mesma stack |
| Código dos serviços | Bind mount + `uvicorn --reload` (hot-reload) | Imagem já construída, sem reload |
| Portas dos serviços | Publicadas no host (`8000-8011`) | Não publicadas — só o `nginx` (gateway) expõe `80`/`443` |
| Arquivo de env | `.env.dev` (copiar de `.env.dev.example`) | `.env.prod` (copiar de `.env.prod.example`, preencher valores reais) |

### Rodar em desenvolvimento

```bash
cp .env.dev.example .env.dev   # uma vez
bash infra/scripts/bootstrap.sh
docker compose -f infra/docker/docker-compose.dev.yml up -d --build
```

### Rodar em produção

```bash
cp .env.prod.example .env.prod   # preencher DB__HOST/PASSWORD reais e demais segredos
docker compose -f infra/docker/docker-compose.prod.yml up -d --build
```

## Scripts (`infra/scripts/`)

- `bootstrap.sh` — cria `.env.dev` se faltar + `uv sync --all-packages`.
- `test-all.sh` / `test-all.ps1` — roda a suíte Pytest de cada `packages/*` e `services/*` isoladamente e agrega o resultado.
- `migrate.sh` — roda `alembic upgrade head` em todo serviço com `alembic/`.
- `create-service-databases.sh` — script de init do container Postgres (dev), cria 1 banco por serviço no mesmo cluster.

## Nginx (`infra/nginx/`)

Gateway usado apenas em `docker-compose.prod.yml`: roteia `/api/v1/<service>/*`
para o microsserviço correspondente e faz o upgrade de protocolo WebSocket em
`/ws/v1/kitchen/*` (KDS). Em dev, os frontends chamam cada serviço
diretamente na sua porta (`VITE_*_URL` em `.env.dev`), sem gateway.

## Kubernetes (`infra/k8s/`)

Manifests de exemplo (não é o alvo principal de deploy desta fase — o
caminho suportado é Docker Compose). `configmap.yaml` e
`menu-service-deployment.yaml` servem como referência do padrão a seguir
caso a plataforma migre para Kubernetes no futuro; os demais 11 serviços
ainda não têm um `Deployment`/`Service` equivalente.
