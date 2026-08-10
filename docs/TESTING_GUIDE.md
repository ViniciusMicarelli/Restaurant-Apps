# 🧪 Guia de Teste Manual — Restaurant Apps Platform

> Gerado em 2026-08-06 após subir o stack completo (19 containers Docker), rodar
> o seeder de demonstração e validar RBAC ponta-a-ponta. Atualizado no mesmo dia
> com a rodada de melhorias (KDS em tempo real, notificações in-app, comanda +
> taxa de serviço, pagamento fake + assinatura, faturamento do dono, QR Code
> rotativo obrigatório). Ver `docs/logs/` para o histórico de decisões
> técnicas; este documento é só o "como testar agora". Atualizado em
> 2026-08-10 com o autoatendimento do cliente (`US-05.4`, §3.2/§4.2).
>
> **Alternativa automatizada**: os roteiros do §5 (Cartão/Pix, garçom e
> cliente) agora também rodam sozinhos via Playwright (`tests/e2e/`,
> `npx playwright test` na raiz — cada spec cria seu próprio tenant, não
> mexe nos dados de demonstração abaixo). Ver `docs/testing/test_strategy.md`.

## 1. Como subir tudo do zero

```powershell
# 1) Infra + 12 microsserviços + workers (Postgres/Redis/RabbitMQ/Meilisearch)
powershell -File infra/scripts/dev-up.ps1

# 2) Seed de dados de demonstração (idempotente — não recria se já existir)
uv run python infra/scripts/seed_demo_data.py

# 3) Os 4 apps de frontend de uma vez (admin-web, customer-web, waiter-mobile,
#    customer-mobile) — cada um numa janela própria. Use -WebOnly pra pular
#    os dois Flutter (mais lentos pra compilar) se só precisar dos web.
powershell -File infra/scripts/apps-up.ps1
```

Equivalente no Bash: `bash infra/scripts/apps-up.sh` (roda cada app em
background com log em `infra/scripts/.apps-logs/<app>.log`; `--web-only` pula
os Flutter; `kill $(cat infra/scripts/.apps-logs/apps.pids.log)` derruba tudo).

Se preferir subir manualmente um de cada vez (útil pra reiniciar só um sem
afetar os outros):

```powershell
cd apps/admin-web && npm run dev       # http://localhost:3001
cd apps/customer-web && npm run dev    # http://localhost:3000

cd apps/waiter-mobile
flutter run -d web-server --web-port=5001 --web-hostname=0.0.0.0 \
  --dart-define=AUTH_SERVICE_URL=http://localhost:8000 \
  --dart-define=RESTAURANT_SERVICE_URL=http://localhost:8001 \
  --dart-define=DINING_SERVICE_URL=http://localhost:8003 \
  --dart-define=MENU_SERVICE_URL=http://localhost:8002 \
  --dart-define=ORDER_SERVICE_URL=http://localhost:8005

cd apps/customer-mobile
flutter run -d web-server --web-port=5002 --web-hostname=0.0.0.0 \
  --dart-define=RESTAURANT_SERVICE_URL=http://localhost:8001 \
  --dart-define=MENU_SERVICE_URL=http://localhost:8002
```

**Nota operacional (achado nesta sessão):** se o Docker Desktop for reiniciado
com os containers já existentes, o RabbitMQ pode ficar pronto DEPOIS dos
serviços que dependem dele (o compose só espera `service_started`, não
`service_healthy`, porque a imagem oficial não define healthcheck). Os serviços
tratam isso deliberadamente (log + segue), mas ficam com o `EventBus`
permanentemente desconectado até reiniciarem. Sintoma: `POST /api/v1/orders`
devolve 500 com `RuntimeError: RabbitMQEventBus.connect() deve ser chamado
antes de publish()`. Correção: `docker restart order-service kitchen-service
inventory-service analytics-service notification-service notification-bridge`
depois que `restaurant-rabbitmq-dev` estiver de pé.

Os `.env.local` de `apps/admin-web` e `apps/customer-web` foram criados nesta
sessão (não existiam) — Vite só lê `.env*` da própria pasta do app, não o
`.env.dev` da raiz do monorepo. Suporte a Flutter Web (`web/`) também foi
adicionado a `apps/waiter-mobile` e `apps/customer-mobile` (`flutter create .
--platforms=web`) — nenhum dos dois tinha a plataforma web habilitada.

---

## 2. Infraestrutura — URLs e credenciais

| Serviço | URL | Credenciais |
|---|---|---|
| RabbitMQ Management UI | http://localhost:15672 | ver `RABBITMQ_USER`/`RABBITMQ_PASS` em `.env.dev` |
| Meilisearch | http://localhost:7700 | header `Authorization: Bearer <MEILI_MASTER_KEY>` (`.env.dev`) |
| PostgreSQL | `localhost:5432` | ver `DB__USER`/`DB__PASSWORD`/`POSTGRES_*` em `.env.dev`; 12 bancos, um por serviço (`auth_db`, `restaurant_db`, `menu_db`, `dining_db`, `orders_db`, `kitchen_db`, `inventory_db`, `payments_db`, `delivery_db`, `marketing_db`, `notifications_db`, `analytics_db`) |
| Redis | `localhost:6379` | sem senha (dev) |

---

## 3. Microsserviços — health check, Swagger e papéis por rota

Todo serviço FastAPI expõe **Swagger UI em `/docs`** e **Redoc em `/redoc`** —
é a forma mais rápida de explorar/testar qualquer endpoint manualmente (botão
"Authorize" aceita o `access_token` do login como Bearer).

| # | Serviço | Porta | Health check | Swagger |
|---|---|---|---|---|
| 1 | auth-service | 8000 | `GET /api/v1/auth/health` | http://localhost:8000/docs |
| 2 | restaurant-service | 8001 | `GET /api/v1/restaurants/health/check` | http://localhost:8001/docs |
| 3 | menu-service | 8002 | `GET /api/v1/menu/health/check` | http://localhost:8002/docs |
| 4 | dining-service | 8003 | `GET /api/v1/dining/health/check` | http://localhost:8003/docs |
| 5 | kitchen-service | 8004 | `GET /api/v1/kitchen/health/check` | http://localhost:8004/docs |
| 6 | order-service | 8005 | `GET /api/v1/orders/health/check` | http://localhost:8005/docs |
| 7 | inventory-service | 8006 | `GET /api/v1/inventory/health/check` | http://localhost:8006/docs |
| 8 | payment-service | 8007 | `GET /api/v1/payments/health/check` | http://localhost:8007/docs |
| 9 | delivery-service | 8008 | `GET /api/v1/deliveries/health/check` | http://localhost:8008/docs |
| 10 | marketing-service | 8009 | `GET /api/v1/marketing/health/check` | http://localhost:8009/docs |
| 11 | notification-service | 8010 | `GET /api/v1/notifications/health/check` | http://localhost:8010/docs |
| 12 | analytics-service | 8011 | `GET /api/v1/analytics/health/check` | http://localhost:8011/docs |

Todos os 12 responderam `200 {"status":"healthy",...}` nesta sessão.

### 3.1 Papéis RBAC do sistema

```
SUPER_ADMIN       — operador da plataforma (multi-tenant, fora do escopo de um restaurante)
RESTAURANT_OWNER  — dono do restaurante (acesso total ao próprio tenant)
MANAGER           — gerente (quase tudo que o Owner faz, exceto o que é Owner-only)
CASHIER           — caixa (abre/fecha caixa, recebe pagamentos, fecha comandas)
WAITER            — garçom (abre comandas, mesas, fila, delivery, cria pedidos)
KITCHEN_STAFF     — cozinha (KDS: só avança status de itens)
CUSTOMER          — cliente final (sem login — cardápio digital público, escopado por tenant via slug/QR Code)
```

Autenticação: `Authorization: Bearer <access_token>` (expira em 15 min;
`refresh_token` dura 7 dias). Rotas públicas (cardápio) usam o header
`X-Tenant-Id` no lugar do JWT.

### 3.2 Endpoints por serviço e quem pode chamar

**auth-service** (`/api/v1/auth`)
| Rota | Quem |
|---|---|
| `POST /register-owner` | Público (único endpoint de escrita sem auth — cadastra o 1º usuário de um tenant novo) |
| `POST /employees` | OWNER, MANAGER |
| `POST /login` | Público (e-mail + senha) |
| `POST /login-pin` | Público (`tenant_id` + PIN de 4 dígitos — usado pelos apps mobile) |
| `POST /refresh` | Público (refresh token válido) |
| `POST /logout` | Autenticado (qualquer papel) |
| `GET /me` | Autenticado (qualquer papel) |

**restaurant-service** (`/api/v1/restaurants`)
| Rota | Quem |
|---|---|
| `POST /` | Público (bootstrap do tenant) |
| `GET /by-slug/{slug}`, `GET /{id}` | Público |
| `PATCH /{id}`, `PUT /{id}/branding` | OWNER, MANAGER (só o próprio tenant) |

**menu-service** (`/api/v1/menu`)
| Rota | Quem |
|---|---|
| `GET /categories`, `GET /products`, `GET /products/{id}`, `GET /products/{id}/addon-groups`, `GET /search` | Público (escopo por `X-Tenant-Id`/JWT — cardápio digital) |
| `POST /categories`, `POST /products`, `PATCH /products/{id}`, `POST /addon-groups` | OWNER, MANAGER |

**dining-service** (`/api/v1/dining`)
| Rota | Quem |
|---|---|
| `POST /tables` | OWNER, MANAGER |
| `GET /tables`, `GET /commands` (opcional `?status=OPEN\|CLOSED`), `GET /queue` | Autenticado (qualquer papel da equipe) |
| `POST /commands/open`, `POST /queue`, `POST /queue/call-next` | OWNER, MANAGER, WAITER |
| `PATCH /commands/{id}/service-fee` (`{"charged": bool}`) | OWNER, MANAGER, WAITER |
| `POST /commands/{id}/close` | OWNER, MANAGER, WAITER, CASHIER |
| `POST /tables/{table_id}/mark-cleaned` | OWNER, MANAGER, WAITER — libera uma mesa `WAITING_CLEANING` de volta pra `AVAILABLE` (2026-08-07) |
| `POST /tables/{table_id}/qr-secret/rotate` | OWNER, MANAGER, WAITER — gera/rotaciona a secret do QR Code da mesa; válida durante todo o ciclo de ocupação (rotaciona sozinha ao encerrar a comanda — ver `CloseCommandUseCase`), TTL de 24h só como rede de segurança |
| `GET /tables/{table_number}/qr-secret/validate?secret=X` | Público (`X-Tenant-Id`) — usado pelo `customer-web` antes de abrir o cardápio |
| `GET /tables/{table_number}/open-command?secret=X` | Público (`X-Tenant-Id` + secret) — autoatendimento do cliente (`US-05.4`, 2026-08-10): dá o `command_id`/`service_fee_charged` da comanda aberta da mesa |
| `POST /commands/{command_id}/customer-close?secret=X` | Público (`X-Tenant-Id` + secret) — cliente fecha a própria comanda (`US-05.4`, 2026-08-10), mesmo efeito de `POST /commands/{id}/close` |

**order-service** (`/api/v1/orders`)
| Rota | Quem |
|---|---|
| `POST /` (aceita `command_id` opcional) | Escopo de tenant (JWT ou `X-Tenant-Id`) — sem restrição de papel (cobre QR Code do cliente) |
| `GET /` (filtros opcionais `?table_number=N` e/ou `?command_id=X`), `GET /{id}` | Escopo de tenant |
| `PATCH /{id}/status` | OWNER, MANAGER, WAITER, KITCHEN_STAFF — publica `order.status_changed` (dispara notificação quando vira `READY`) |
| `POST /{id}/cancel` | OWNER, MANAGER |

**kitchen-service** (sem prefixo comum — rotas absolutas)
| Rota | Quem |
|---|---|
| `GET /api/v1/kitchen/kds/items` (agora inclui `created_at`) | OWNER, MANAGER, KITCHEN_STAFF |
| `PATCH /api/v1/kitchen/kds/items/{id}/status` | OWNER, MANAGER, KITCHEN_STAFF |
| `WS /ws/v1/kitchen/kds?token=<access_token>` | OWNER, MANAGER, KITCHEN_STAFF — tempo real, broadcast por tenant; **agora consumido de verdade pelo `admin-web`** |

**inventory-service** (`/api/v1/inventory`)
| Rota | Quem |
|---|---|
| Todas (`/items`, `/items/{id}/movements`, `/items/{id}/count`, `/suppliers`, `/recipes`, `/recipes/{product_id}`) | OWNER, MANAGER |

**payment-service** (`/api/v1/payments`)
| Rota | Quem |
|---|---|
| `POST /cash-registers`, `GET /cash-registers/mine`, `POST /cash-registers/{id}/close`, `POST /` (processar pagamento) | OWNER, MANAGER, CASHIER, **WAITER** (cobra na mesa com a própria maquininha — abre/fecha só o próprio caixa) |
| `GET /cash-registers/{id}` (por ID), `GET/POST /cash-registers/{id}/movements` (sangria/suprimento) | OWNER, MANAGER, CASHIER — auditoria mais ampla, **WAITER não tem acesso** |
| `GET /` (opcional `?status=APPROVED\|PENDING\|FAILED\|REFUNDED`), `GET /{id}` | OWNER, MANAGER, CASHIER |
| `POST /customer-checkout` | Público (`X-Tenant-Id` + `table_number`/`secret` no corpo) — autoatendimento do cliente (`US-05.4`, 2026-08-10): paga sem caixa (`cash_register_id=null`), só Cartão/Pix (Dinheiro é rejeitado); autoriza validando a secret da mesa contra o `dining-service` |

**delivery-service** (`/api/v1/deliveries`)
| Rota | Quem |
|---|---|
| Todas | OWNER, MANAGER, WAITER |

**marketing-service** (`/api/v1/marketing`)
| Rota | Quem |
|---|---|
| `POST /coupons` | OWNER, MANAGER |
| `GET /coupons` | OWNER, MANAGER |
| `POST /coupons/apply` | qualquer papel autenticado (aplicado no momento do pedido) |

**notification-service** (`/api/v1/notifications`)
| Rota | Quem |
|---|---|
| `POST /templates` (canais: `EMAIL`, `WHATSAPP`, `PUSH`, `IN_APP`) | OWNER, MANAGER |
| `POST /`, `GET /` (agora inclui `rendered_body` e `created_at`) | OWNER, MANAGER, CASHIER, WAITER, KITCHEN_STAFF |
| — | Além da API manual, o serviço agora **consome o evento `order.status_changed`** automaticamente: pedido vira `READY` → notificação `ORDER_READY` (`IN_APP`) é enfileirada sozinha, sem chamada manual. |

**analytics-service** (`/api/v1/analytics`)
| Rota | Quem |
|---|---|
| `GET /audit-logs` | OWNER, MANAGER |

Confirmado nesta sessão com testes negativos reais contra o stack vivo:
Garçom tentando criar categoria de cardápio → `403`; Cozinha tentando
cadastrar mesa → `403`; requisição sem token ao mapa de mesas → `401`;
Garçom lendo mapa de mesas → `200` (permitido). **Atualizado em 2026-08-06**:
Garçom agora *pode* abrir o próprio caixa (`POST /cash-registers`) e
processar pagamento — só continua bloqueado em endpoints de auditoria mais
ampla, como `GET /cash-registers/{id}` de outro operador → `403`.

### 3.3 Máquinas de estado (enums) úteis para testar transições

- **Mesa** (`TableStatus`): `AVAILABLE → OCCUPIED → WAITING_CLEANING → AVAILABLE`, ou `RESERVED`.
- **Pedido** (`OrderStatus`): `PENDING → PREPARING → READY → DELIVERED`, ou `CANCELLED`.
- **Tipo de pedido** (`OrderType`): `TABLE`, `COUNTER`, `QR_CODE`, `DELIVERY`.
- **Item do KDS** (`KDSItemStatus`): `PENDING → PREPARING → READY → DELIVERED`.
- **Pagamento** (`PaymentStatus`): `PENDING → APPROVED`, ou `FAILED`/`REFUNDED`. Métodos (`PaymentMethod`): `CREDIT_CARD`, `DEBIT_CARD`, `PIX`, `CASH`, `VOUCHER`.
- **Caixa** (`CashMovementType`): `OPENING_FLOAT`, `SALE`, `SANGRIA`, `SUPPLY`.
- **Entrega** (`DeliveryStatus`): `PENDING → ASSIGNED → IN_TRANSIT → DELIVERED`, ou `CANCELLED`.

---

## 4. Apps — URLs e views implementadas hoje

### 4.1 `admin-web` — Painel do Gestor & POS (React/Vite)
**URL**: http://localhost:3001
**Login**: e-mail + senha (`POST /api/v1/auth/login`) — pensado para Owner/Manager
(mas Garçom/Caixa/Cozinha também têm senha, além do PIN, e podem entrar aqui).
Não há roteador (`react-router`); é uma SPA de abas alternadas por estado de sessão:

| View | Como chegar | O que mostra/faz | Visível para |
|---|---|---|---|
| **Login** | tela inicial se não autenticado | formulário e-mail/senha | — |
| **Painel de Controle Operacional** | aba "Dashboard" (padrão pós-login) | taxa de serviço, itens pendentes no KDS, mesas ocupadas/total, moeda | qualquer papel |
| **Mapa de Mesas & Comandas** | aba "Mesas" | grade de mesas coloridas por status; botão **"+ Nova Mesa"**; ícone 🔳 por mesa abre o **QR Code rotativo**; clicar numa mesa `OCCUPIED` abre a **Comanda**; botão **"Mesa Limpa"** numa mesa `WAITING_CLEANING` libera ela de volta pra `AVAILABLE` (2026-08-07) | qualquer papel (criar mesa: só OWNER/MANAGER) |
| **Comanda** (drawer lateral) | clicar numa mesa ocupada | pedidos lançados + total, toggle **"Taxa de serviço cobrada"**, botão **"Fechar e Cobrar"** | qualquer papel (toggle); fechar exige caixa aberto (OWNER/MANAGER/CASHIER/**WAITER**, cada um só vê/abre o próprio) |
| **Pagamento + Assinatura** (modal) | "Fechar e Cobrar" na Comanda | se não houver caixa aberto do usuário, botão **"Abrir meu caixa"** primeiro; depois cartão fake (número/titular/validade/CVV, com efeito de flip) + assinatura em `<canvas>` — nunca envia PAN/CVV completos ao backend | OWNER/MANAGER/CASHIER/WAITER |
| **QR Code da Mesa** (modal) | ícone 🔳 no card da mesa | QR válido durante todo o atendimento da mesa (rotaciona sozinho só quando a comanda é encerrada) + URL copiável em texto + botão manual "Gerar novo código" | qualquer papel (gerar: OWNER/MANAGER/WAITER) |
| **KDS (Kitchen Display System)** | aba "KDS" | itens pendentes/em preparo/prontos, cronômetro "há Xmin" ao vivo (fica amarelo/vermelho com o atraso), botão "Avançar para X"; atualiza via WebSocket + polling | qualquer papel |
| **Faturamento** | aba "Faturamento" | faturamento total (soma de pagamentos aprovados), taxa de serviço total, nº de comandas fechadas, lista de comandas fechadas com taxa | **só RESTAURANT_OWNER** |
| **Personalização White-Label** | aba "Branding" | cor primária (hex) e URL da logo, salva via `PUT /restaurants/{id}/branding` | qualquer papel |
| **Sino de Notificações** | ícone no header | lista de notificações (hoje: "Pedido da Mesa N está pronto!"), atualiza a cada 5s | qualquer papel |

### 4.2 `customer-web` — Cardápio Digital (React/Vite)
**URL**: `http://localhost:3000/?r=<slug>&table=<N>&secret=<secret-da-mesa>`

⚠️ **O QR Code por mesa agora é obrigatório** — o link estático antigo
(`?r=restaurante-demo&table=1`, sem `secret`) **não abre mais o cardápio**.
Gere um link válido pelo `admin-web` (Mesas → ícone 🔳 na mesa → copiar a URL
mostrada) — a secret fica válida durante todo o atendimento da mesa e só
rotaciona automaticamente quando o garçom encerra a comanda (não expira em
segundos como antes). Sem login (papel `CUSTOMER`), mas agora com um gate de
sessão por mesa.

| View | Como chegar | O que mostra |
|---|---|---|
| **QR Code inválido/expirado** | secret ausente, errada ou vencida | tela bloqueante: "Peça a um garçom para gerar um novo QR Code" |
| **Cardápio** (`CustomerMenuPage`) | secret válida | header com branding, carrossel de categorias, grade de produtos, barra flutuante de carrinho (carrinho ainda é local — sem checkout próprio de pedido nesta fase, só de pagamento — ver abaixo) |
| **Meu Pedido** (painel lateral) | botão "Meu Pedido" no topo | pedidos da mesa com itens e status ao vivo (`Recebido`/`Em preparo`/`Pronto`/`Entregue`), polling 5s — mostra o que o garçom já lançou pela comanda; botão **"Fechar minha conta"** no rodapé assim que há ≥1 pedido |
| **Fechar minha conta** (modal, `US-05.4`, 2026-08-10) | botão "Fechar minha conta" no painel "Meu Pedido" | seletor Cartão/Pix (sem Dinheiro, sem assinatura), total já com taxa de serviço se marcada; ao aprovar, fecha a própria comanda e mostra "Obrigado pela visita!" — canal **complementar** ao "Fechar e Cobrar" do garçom no `admin-web`, não o substitui |

### 4.3 `waiter-mobile` — App do Garçom (Flutter)
**URL (Flutter Web, esta sessão)**: http://localhost:5001
**Login**: PIN de 4 dígitos + **código do restaurante** (slug, ex:
`restaurante-demo` — **não é mais preciso digitar o `tenant_id` em UUID**,
o app resolve por trás via `GET /restaurants/by-slug/{slug}`).

| View | Como chegar | O que faz |
|---|---|---|
| **Login por PIN** | tela inicial se não houver sessão | campo "Código do restaurante" (slug) + teclado numérico de 4 dígitos |
| **Mapa de Mesas** (`TableMapScreen`) | pós-login | grade de mesas do salão; tocar numa mesa `WAITING_CLEANING` libera ela de volta pra `AVAILABLE` (2026-08-07) |
| **Abrir Comanda** (`OpenCommandScreen`) | a partir de uma mesa livre | nome do cliente, CPF opcional — segue direto para montar o pedido, já com o `command_id` vinculado |
| **Montar Pedido** (`BuildOrderScreen`) | a partir de uma comanda (aberta agora ou já `OCCUPIED`) | seleção de produtos do cardápio, quantidade, envia `POST /orders` já com `command_id` (soma no total da comanda/faturamento) |

### 4.4 `customer-mobile` — App do Cliente (Flutter)
**URL (Flutter Web, esta sessão)**: http://localhost:5002
Sem login (papel `CUSTOMER`, público).

| View | Como chegar | O que faz |
|---|---|---|
| **Seleção de Restaurante** (`RestaurantSelectionScreen`) | tela inicial | campo de texto para o `slug` do restaurante (em produção viria de um QR Code/deep link) |
| **Cardápio** (`MenuScreen`) | após informar o slug | categorias e produtos |
| **Detalhe do Produto** (`ProductDetailScreen`) | ao tocar num produto | descrição, preço, adicionais |

---

## 5. Dados de demonstração (seeder)

Script: `infra/scripts/seed_demo_data.py` (`uv run python infra/scripts/seed_demo_data.py`).
Não-destrutivo: se o restaurante já existir, ele avisa e não recria nada.

**Restaurante**: Restaurante Demo — slug `restaurante-demo` (é isso que se
digita no login por PIN do `waiter-mobile` e no `customer-mobile` — **não** o
`tenant_id`/UUID, que o app resolve por trás via `GET /restaurants/by-slug`)

| Papel | E-mail | Senha | PIN |
|---|---|---|---|
| RESTAURANT_OWNER | dono@restaurantedemo.com.br | `Demo@12345` | — |
| MANAGER | gerente@restaurantedemo.com.br | `Demo@12345` | `1111` |
| CASHIER | caixa@restaurantedemo.com.br | `Demo@12345` | `2222` |
| WAITER | garcom@restaurantedemo.com.br | `Demo@12345` | `3333` |
| KITCHEN_STAFF | cozinha@restaurantedemo.com.br | `Demo@12345` | `4444` |

Também criados: 5 mesas (1–5), 3 categorias/5 produtos de cardápio, 3 insumos
de estoque, 1 cupom (`DEMO10`, 10% off), o template de notificação
`ORDER_READY` (`IN_APP`), uma comanda aberta na Mesa 1, **um pedido de R$
72,80 já em andamento** (2× X-Burger Demo + 2× Refrigerante Lata — confirmado
populando o KDS via Saga em ~1s) e **um caixa aberto com R$ 200,00**. O
pedido foi deixado `PENDING` de pagamento de propósito, para testar o fluxo
de pagamento manualmente.

Roteiro sugerido de teste ponta-a-ponta (cobrindo a rodada de melhorias):
1. `admin-web` → login como Owner → Mesas → gerar o QR Code da Mesa 1 → copiar a URL.
2. Abrir a URL copiada em outra aba → cardápio do `customer-web` abre normalmente; abrir sem `secret` (link antigo) → tela "QR Code inválido/expirado".
3. `waiter-mobile` → login por PIN (slug `restaurante-demo`, PIN do Garçom) → Mesa 2 (livre) → abrir comanda → lançar um pedido.
4. `admin-web` → aba KDS → cronômetro sobe ao vivo no item novo → avançar `PENDING → PREPARING → READY` → sino de notificações mostra "Pedido da Mesa 2 está pronto!" em até 5s.
5. `customer-web` (aba "Meu Pedido" da Mesa 2) → status reflete `READY` sem precisar recarregar a página.
6. `admin-web` → Mesas → clicar na Mesa 2 (ocupada) → drawer da Comanda → ligar "Taxa de serviço cobrada" → "Fechar e Cobrar" → preencher cartão fake + assinar → confirmar pagamento.
7. `admin-web` → aba Faturamento (só aparece para o Owner) → valor pago e taxa de serviço refletidos.
8. **Autoatendimento do cliente** (`US-05.4`, alternativa ao passo 6): em vez de fechar pela maquininha no `admin-web`, abrir "Meu Pedido" no `customer-web` da Mesa 2 → "Fechar minha conta" → pagar por Cartão ou Pix → confirma que a comanda fecha e a mesa vai pra `WAITING_CLEANING` igual ao fluxo do garçom. Testar também a corrida: fechar pela maquininha primeiro e depois tentar pelo `customer-web` (ou vice-versa) → o segundo canal mostra uma mensagem amigável, não erro cru.

---

## 6. Detalhe técnico da rodada de melhorias (2026-08-06)

Tudo abaixo foi implementado, migrado e verificado ponta-a-ponta contra o
stack vivo nesta sessão (não é só código — cada item tem um teste real via
`curl`/`httpx` confirmando o comportamento).

### 6.1 KDS em tempo real
`KDSItem`/`Order` ganharam `created_at` exposto (a coluna já existia via
`BaseDBModel`, só nunca tinha chegado ao DTO). `admin-web` agora consome de
verdade o WebSocket `/ws/v1/kitchen/kds` (existia no backend desde sempre,
nunca tinha sido usado por nenhum frontend) — o polling REST de 5s continua
como rede de segurança. O cronômetro "há Xmin" é `setInterval` client-side,
fica amarelo aos 5min e vermelho aos 10min sem avançar.

### 6.2 Notificações — o gatilho que faltava
Diagnóstico: notificações nunca disparavam porque **nada publicava um
evento** quando um pedido ficava pronto (`TransitionOrderStatusUseCase` nem
dependia do `EventBus`), e o `notification-service` só existia como API REST
— nunca como consumidor de eventos. Agora: `order-service` publica
`order.status_changed` a cada transição; `notification-service` passou a
assinar esse evento (mesmo padrão do `kitchen-service` para `order.created`)
e, quando `new_status == READY`, enfileira a notificação `ORDER_READY`
automaticamente. Canal novo `IN_APP` (além de `EMAIL`/`WHATSAPP`/`PUSH`) —
sem provedor externo, o "envio" continua sendo um log estruturado
(`NOTIFICATION_SENT (simulado)`, decisão de escopo já documentada no próprio
código), mas agora o sino do `admin-web` mostra a notificação de verdade.
**Requer o template `ORDER_READY` cadastrado por tenant** (o seeder já cria
para o tenant demo) — sem ele, o handler apenas ignora silenciosamente
(loga um aviso) em vez de quebrar o consumidor.

### 6.3 Comanda ↔ Pedido, taxa de serviço, criar mesa
`Order` ganhou `command_id` opcional (order-service); `GET /orders` ganhou
filtros `table_number`/`command_id`. `Command` ganhou `service_fee_charged`
(bool, alternável pelo garçom a qualquer momento antes do fechamento via
`PATCH .../service-fee`). `waiter-mobile` já passa o `command_id` certo ao
montar um pedido (tanto ao abrir uma comanda nova quanto ao lançar mais um
pedido numa mesa já ocupada — nesse caso busca a comanda aberta da mesa via
`GET /commands?status=OPEN` antes de navegar). `admin-web` ganhou seu
primeiro gate por papel (`session.user.role`) para o botão "+ Nova Mesa"
(OWNER/MANAGER) e para a aba Faturamento (OWNER).

### 6.4 Pagamento fake + assinatura
Pagamento já era 100% simulado (`ProcessPaymentUseCase` nunca chamou gateway
real — não havia nada a "fingir"). Adicionado: `card_last4`,
`card_holder_name`, `signature_data` (PNG base64) em `Payment`, persistidos
no Postgres. **Nunca** persiste PAN completo nem CVV — só os 4 últimos
dígitos, mesmo em modo fake (mesmo princípio de um gateway real). Novo
endpoint `GET /cash-registers/mine` (caixa aberto do usuário logado, sem
precisar saber o UUID). Componente novo `PaymentSignatureForm` no
`admin-web`: cartão reescrito em Tailwind (o projeto usa Vite puro, sem
Next.js — `<style jsx>` do componente colado pelo usuário não funcionaria
aqui) e assinatura em `<canvas>` nativo (sem a dependência `@ark-ui/react`,
não instalada no projeto — evita adicionar uma lib nova só para isso).

**Limitação conhecida — resolvida em 2026-08-10**: o modelo de `Payment`
referenciava um único `order_id`, e uma comanda com múltiplos pedidos
lançados usava o *primeiro* pedido como referência ao pagar pela Comanda no
`admin-web` (o valor cobrado sempre foi o total certo, somando todos os
pedidos; só o campo de rastreio `order_id` do registro de pagamento não
refletia todos). Corrigido com a refatoração "Payment por Comanda":
`Payment.command_id` (novo, opcional) passou a ser a referência autoritativa
da comanda paga — ver `docs/CHANGELOG.md` de 2026-08-10.

### 6.5 Faturamento do dono
Novo `GET /api/v1/payments` (lista, filtro por `status`) e
`GET /api/v1/dining/commands?status=CLOSED`. Sem `analytics-service`
dedicado para isso (hoje só tem `AuditLog`) — a aba Faturamento agrega no
cliente: soma pagamentos `APPROVED` (faturamento total) + para cada comanda
fechada com `service_fee_charged=true`, soma o total dos pedidos daquela
comanda (`GET /orders?command_id=`) × `restaurant.service_fee_percent`
(esse campo já existia desde o início, mas nunca era usado em cálculo algum
em lugar nenhum do sistema — primeira vez que é de fato aplicado).

### 6.6 QR Code rotativo por mesa (obrigatório)
Antes: link estático `?r=slug&table=N`, sem nenhuma secret. Agora: `Table`
ganhou `active_qr_secret`/`qr_secret_expires_at` (`secrets.token_urlsafe`,
não JWT — comparar um segredo opaco não precisa da máquina de claims/roles
do `restaurant_security`, então evitou estender esse pacote compartilhado
para um caso de uso mais simples). Rotação (~90s) só acontece enquanto o
modal do QR estiver aberto no `admin-web` (sem cron/scheduler novo no
backend — a própria tela pede uma secret nova a cada 75s). `customer-web`
valida a secret uma única vez ao carregar (`GET
/tables/{number}/qr-secret/validate`) e bloqueia o cardápio se ausente,
errada ou expirada.

### 6.7 UX do login por PIN corrigida
Pedido do usuário durante a sessão: digitar um `tenant_id` (UUID) de cabeça
para logar é inviável na prática. `waiter-mobile` agora pede o **slug** do
restaurante (o mesmo que aparece na URL do cardápio, ex: `restaurante-demo`)
e resolve o UUID por trás via `GET /restaurants/by-slug/{slug}` (endpoint
público, já existente) antes de chamar o login por PIN. `customer-mobile` já
usava slug desde o início — não precisou de ajuste.

### 6.8 Verificação executada nesta sessão
`uv run ruff check .` / `ruff format --check .` limpos no workspace inteiro;
`mypy --strict` limpo em todos os serviços tocados (only o erro pré-existente
`Column` sem type-arg em `alembic/versions/0001_initial_schema.py` de cada
serviço, que já existia antes desta rodada); suíte `pytest` completa
passando em `order-service` (32), `dining-service` (25), `payment-service`
(41), `notification-service` (19), `kitchen-service` (31); `tsc --noEmit`
limpo em `admin-web` e `customer-web`; `flutter analyze` limpo em
`waiter-mobile`. Fluxos completos testados via `httpx` contra o stack Docker
vivo: KDS timer, notificação automática em `READY`, `command_id` em pedidos,
taxa de serviço, pagamento com cartão fake + assinatura persistidos no
Postgres, faturamento agregado, e rotação/validação do QR Code da mesa.

---

## 7. Correções da noite de 2026-08-06 (dois bugs relatados)

Ver `docs/logs/2026-08-06.md` para o diagnóstico completo. Resumo do que
mudou (supera o comportamento descrito nas seções 3.2/4.1/4.2/6.6 acima):

**QR Code da mesa não expira mais em ~90s.** `Table.rotate_qr_secret()` só
é chamada automaticamente por `CloseCommandUseCase`, quando a comanda é
encerrada — a secret fica válida durante todo o ciclo de ocupação da mesa.
Um TTL de 24h continua existindo só como rede de segurança (mesa esquecida
aberta), não como mecanismo principal. `TableQrModal` (admin-web) não
re-rotaciona mais a cada 75s; gera uma vez ao abrir e tem um botão manual
"Gerar novo código" pra forçar uma nova (ex: suspeita de vazamento).

**Garçom (`WAITER`) agora processa pagamento e fecha comanda.** Modela a
maquininha física que ele carrega até a mesa: `payment-service` passou a
aceitar `WAITER` em `POST /cash-registers` (abrir o próprio caixa),
`GET /cash-registers/mine`, `POST /cash-registers/{id}/close` e
`POST /payments` (processar). A auditoria mais ampla (`GET
/cash-registers/{id}` de qualquer operador, `GET/POST .../movements`, listar
todos os pagamentos do tenant) continua restrita a OWNER/MANAGER/CASHIER.
`CheckoutModal` (admin-web) ganhou um botão real **"Abrir meu caixa"**
(`opening_amount=0`, já que é fluxo 100% cartão) no lugar do texto cru com o
comando `curl` que existia antes — não havia nenhuma UI pra isso, pra
nenhum papel.

A ideia de o **cliente pagar direto no `customer-web`** quando o garçom
encerra a mesa (canal alternativo à maquininha) foi registrada como
`US-05.4` em `docs/BACKLOG.md`/`docs/ROADMAP.md` — não implementada nesta
rodada.
