# 🚂 Guia de Setup — Deploy na Railway

> Complementa `infrastructure_strategy.md`. Passo a passo pra criar os
> serviços no painel da Railway — não é automatizável a partir daqui (sem
> acesso ao painel/CLI autenticado), então este guia é a "receita" pra
> aplicar manualmente uma vez. Depois de criado, cada `git push` em
> `staging`/`main` dispara redeploy automático (Railway já observa o
> repositório GitHub).

## 0. Antes de começar

- Repositório já tem tudo que a Railway precisa: `railway.json` ao lado
  de cada `Dockerfile` (17 no total — 12 microsserviços, `admin-web`,
  `customer-web`, e 3 arquivos `workers/railway.<processo>.json` pros
  processos que compartilham `workers/Dockerfile`).
- **Environments da Railway = branches**: crie 2 environments no projeto
  (`staging` → branch `staging`, `production` → branch `main`) — a
  Railway redeploya sozinha a cada push na branch mapeada.
- Nenhum serviço expõe porta fixa: todo `Dockerfile` já lê `$PORT`
  dinamicamente (ajustado nesta rodada — CMD em forma shell, não exec).
  A Railway injeta `PORT` sozinha, não precisa setar.

## 1. Plugins gerenciados

| Recurso | Como criar | Observação |
|---|---|---|
| **PostgreSQL** | "New" → "Database" → "PostgreSQL" | Uma instância só, várias databases (Database-per-Service já é o padrão do projeto — cada serviço aponta pro mesmo host, `DB__NAME` diferente). Depois de criar, rodar as migrations de cada serviço uma vez (`alembic upgrade head` — via Railway CLI `railway run` ou um job de deploy). |
| **Redis** | "New" → "Database" → "Redis" | Uma instância só, `REDIS__DB` (0-12) separa por serviço, mesmo padrão do Compose. |
| **RabbitMQ** | "New" → "Empty Service" → imagem `rabbitmq:3-management-alpine` | Sem plugin oficial da Railway — sobe como serviço a partir da imagem pública, com um volume anexado. Guardar host/porta/usuário/senha como Shared Variables. |
| **Meilisearch** | "New" → "Empty Service" → imagem `getmeili/meilisearch:v1.6` | Mesmo caso do RabbitMQ — sem plugin oficial, sobe da imagem pública + volume. |

## 2. Shared Variables (nível do projeto)

Railway deixa declarar variáveis uma vez no projeto e referenciar em
cada serviço com `${{shared.NOME}}` — evita repetir segredo em 17
lugares. Baseado em `.env.prod.example`:

| Shared Variable | Valor |
|---|---|
| `JWT_SECRET_KEY` | mesmo segredo pra todos os serviços (validação local do JWT, `docs/ai/architecture.md`) |
| `DB__HOST` / `DB__PORT` / `DB__USER` / `DB__PASSWORD` | `${{Postgres.PGHOST}}` / `${{Postgres.PGPORT}}` / `${{Postgres.PGUSER}}` / `${{Postgres.PGPASSWORD}}` (referência direta ao plugin, não copiar valor) |
| `REDIS_HOST` / `REDIS_PORT` | `${{Redis.REDISHOST}}` / `${{Redis.REDISPORT}}` |
| `RABBITMQ_HOST` / `RABBITMQ_PORT` / `RABBITMQ_USER` / `RABBITMQ_PASS` | do serviço RabbitMQ criado no passo 1 |
| `MEILI_MASTER_KEY` / `MEILISEARCH_URL` | do serviço Meilisearch criado no passo 1 |
| `ENVIRONMENT` | `production` (environment de produção) / `staging` (environment de staging) |
| `DEBUG` | `false` |

## 3. Cada um dos 17 serviços deployáveis

Pra cada linha da tabela: "New" → "GitHub Repo" → seleciona este repo →
nas Settings do serviço:
- **Root Directory**: deixar vazio/`.` (raiz do repo) — **nunca** o
  subdiretório do serviço. Os `Dockerfile` exigem contexto = raiz por
  causa do workspace `uv` (ver comentário no topo de cada um).
- **Config File Path**: aponta pro `railway.json` do serviço (Railway só
  lê automaticamente um `railway.json` na raiz — como cada serviço tem o
  seu ao lado do próprio `Dockerfile`, esse campo é obrigatório setar
  manualmente por serviço, senão a Railway ignora o arquivo).

| Serviço | Config File Path | Variáveis extras (além das Shared) |
|---|---|---|
| auth-service | `services/auth-service/railway.json` | `DB__NAME=auth_db`, `REDIS__DB=0` |
| restaurant-service | `services/restaurant-service/railway.json` | `DB__NAME=restaurant_db`, `REDIS__DB=1` |
| menu-service | `services/menu-service/railway.json` | `DB__NAME=menu_db`, `REDIS__DB=2`, `MEILISEARCH_URL` |
| dining-service | `services/dining-service/railway.json` | `DB__NAME=dining_db`, `REDIS__DB=3` |
| kitchen-service | `services/kitchen-service/railway.json` | `DB__NAME=kitchen_db`, `REDIS__DB=5` |
| order-service | `services/order-service/railway.json` | `DB__NAME=orders_db`, `REDIS__DB=4`, `DINING_SERVICE_URL`/`RESTAURANT_SERVICE_URL` (domínio interno Railway do respectivo serviço) |
| inventory-service | `services/inventory-service/railway.json` | `DB__NAME=inventory_db`, `REDIS__DB=6` |
| payment-service | `services/payment-service/railway.json` | `DB__NAME=payments_db`, `REDIS__DB=7`, `DINING_SERVICE_URL`/`ORDER_SERVICE_URL`/`RESTAURANT_SERVICE_URL` |
| delivery-service | `services/delivery-service/railway.json` | `DB__NAME=delivery_db`, `REDIS__DB=10` |
| marketing-service | `services/marketing-service/railway.json` | `DB__NAME=marketing_db`, `REDIS__DB=11` |
| notification-service | `services/notification-service/railway.json` | `DB__NAME=notifications_db`, `REDIS__DB=8` |
| analytics-service | `services/analytics-service/railway.json` | `DB__NAME=analytics_db`, `REDIS__DB=9` |
| dramatiq-worker | `workers/railway.dramatiq-worker.json` | `REDIS__DB=12` |
| notification-bridge | `workers/railway.notification-bridge.json` | `REDIS__DB=12` |
| scheduler | `workers/railway.scheduler.json` | `REDIS__DB=12` |
| admin-web | `apps/admin-web/railway.json` | **Build-time** (ver §4): `VITE_AUTH_SERVICE_URL`, `VITE_RESTAURANT_SERVICE_URL`, `VITE_DINING_SERVICE_URL`, `VITE_KITCHEN_SERVICE_URL`, `VITE_KITCHEN_WS_URL`, `VITE_ORDER_SERVICE_URL`, `VITE_PAYMENT_SERVICE_URL`, `VITE_NOTIFICATION_SERVICE_URL`, `VITE_CUSTOMER_WEB_URL` |
| customer-web | `apps/customer-web/railway.json` | **Build-time**: `VITE_RESTAURANT_SERVICE_URL`, `VITE_MENU_SERVICE_URL`, `VITE_DINING_SERVICE_URL`, `VITE_ORDER_SERVICE_URL`, `VITE_PAYMENT_SERVICE_URL` (`VITE_DEFAULT_RESTAURANT_SLUG` fica em branco, ver comentário em `.env.prod.example`) |

Os 3 workers não precisam de domínio público (não são serviços HTTP) —
na Railway, "Generate Domain" fica opcional/desligado pra eles.

Os `DB__NAME`/`REDIS__DB` de cada serviço espelham exatamente
`.env.prod.example` (`AUTH_DB_NAME`, `AUTH_REDIS_DB`, etc.) — mesmos
valores, só o nome da variável muda (`__` no lugar de `_` porque é assim
que o `pydantic-settings` do projeto lê configs aninhadas, ver
`restaurant_common.settings.build_settings_config`).

## 4. Variáveis de build (só `admin-web`/`customer-web`)

O Vite embute `VITE_*` no bundle estático **em build time**, não lê em
runtime — diferente de todas as variáveis Python (`DB__*`, `REDIS__*`
etc, essas sim lidas em runtime). Na Railway, isso significa: as
variáveis `VITE_*` de cada um dos 2 web apps precisam estar marcadas
como **disponíveis no build** (não é o padrão — por default a Railway só
injeta variáveis no container em runtime). No painel do serviço,
Settings → Variables, cada `VITE_*` tem um toggle "Available at
Build Time" — ativar pros 2 web apps. Os `Dockerfile` já declaram os
`ARG`/`ENV` correspondentes (ajustado nesta rodada); sem isso o build
funciona mas o bundle final não tem as URLs reais.

## 5. Health checks

Já configurados via `deploy.healthcheckPath` em cada `railway.json` —
nada a fazer manualmente, só conferir que o campo "Healthcheck Path" nas
Settings do serviço reflete o que veio do arquivo (a Railway costuma
preencher sozinha ao detectar o `railway.json`, mas vale conferir depois
do primeiro deploy). Nota: os paths **não são uniformes** entre serviços
(`auth-service` usa `/api/v1/auth/health`, o resto usa
`.../health/check`) — inconsistência pré-existente do projeto, não um
erro deste guia.

## 6. Migrations

Nenhum serviço roda `alembic upgrade head` sozinho no boot (decisão
deliberada, evita duas réplicas migrando ao mesmo tempo). Depois do
primeiro deploy de cada serviço com banco (todos exceto os 3 workers),
rodar uma vez via Railway CLI:

```
railway run --service auth-service alembic upgrade head
```

(repetir por serviço — só na primeira vez / a cada nova migration).

## 7. Ordem recomendada do primeiro deploy

1. Plugins (Postgres, Redis) + serviços RabbitMQ/Meilisearch da imagem pública.
2. Shared Variables (§2).
3. `auth-service` sozinho primeiro — confirma que Postgres/Redis/JWT
   estão certos antes de espalhar pros outros 11.
4. Resto dos microsserviços + os 3 workers.
5. `admin-web`/`customer-web` por último (dependem das URLs públicas dos
   serviços acima já estarem estáveis).
6. Migrations (§6) em cada serviço com banco.
