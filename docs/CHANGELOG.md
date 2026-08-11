# 📝 Histórico de Mudanças (Changelog) — Restaurant Apps Platform

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [Unreleased] — 2026-08-10

### Adicionado — CI/CD + preparação pra deploy na Railway
* **Git inicializado nesta sessão** (repo vinculado a
  `github.com/ViniciusMicarelli/Restaurant-Apps`) — commit inicial (todo o
  código existente) na branch `main`, `staging` criada a partir dela, e
  todo o trabalho desta seção numa branch de trabalho
  (`chore/ci-and-railway-setup`), nunca commitado direto em `main`/`staging`.
* **Dockerfiles ajustados pra Railway**: os 12 `services/*/Dockerfile`
  tinham `CMD` em forma exec com porta hardcoded — a aplicação já lia
  `PORT` corretamente via `BaseAppSettings`, só o Dockerfile ignorava.
  Trocado pra forma shell (`CMD ["sh", "-c", "uvicorn ... --port
  ${PORT:-XXXX}"]`), mesmo ajuste no `HEALTHCHECK`. Sem mudança de
  comportamento em `docker compose` dev/prod (ambos sempre setam `PORT`
  explicitamente) — verificado ao vivo (rebuild + restart do
  `auth-service` no stack dev, `200 OK`) e via container standalone com
  `PORT` customizado.
* **`Dockerfile` novos**: `apps/admin-web` e `apps/customer-web` não
  tinham nenhum — multi-stage `node:20-alpine` (build) → `nginx:1.27-alpine`
  (serve `dist/` estático), porta via `${PORT}` resolvida em runtime pelo
  entrypoint padrão da imagem Nginx (`envsubst` sobre
  `nginx.conf.template`). `VITE_*` (embutido no bundle em build time, não
  runtime) vira `ARG`/`ENV` no Dockerfile — documentado que precisa
  marcar "Available at Build Time" na Railway. Testado com build real +
  container rodando numa porta customizada (`200 OK`).
* **`railway.json`** (config-as-code, formato oficial): um por serviço
  deployável — 12 microsserviços, `admin-web`, `customer-web`, e 3
  arquivos `workers/railway.<processo>.json` (o mesmo `workers/Dockerfile`
  vira 3 serviços Railway via `deploy.startCommand` diferente, mesmo
  padrão do `command:` já usado no `docker-compose.prod.yml`).
  `deploy.healthcheckPath` de cada um reflete o path real (inclui a
  inconsistência já conhecida `/health` vs `/health/check`).
* **`.github/workflows/ci.yml`** (novo): lint (ruff, 1x pro workspace) +
  `mypy --strict`/`pytest` por serviço/pacote/worker (matriz, 18
  entradas — testes de integração usam SQLite em memória, sem precisar
  de Postgres real no runner) + build/test dos 2 web apps + `flutter
  analyze`/`test` dos 2 apps mobile + build Docker de amostra (sem push).
  Roda em PR contra `staging`/`main` e em push nas duas.
* **`.github/dependabot.yml`** (novo): `uv` (workspace), `npm`×3, `pub`×2,
  `docker`×15, `github-actions` — todos mirando `staging`, passam pelo
  mesmo CI antes de `main`.
* **`.env.prod.example`**: corrigido pra incluir `VITE_*` que o código já
  usava mas o arquivo nunca listou (`VITE_CUSTOMER_WEB_URL`,
  `VITE_NOTIFICATION_SERVICE_URL`, `VITE_MENU_SERVICE_URL`,
  `VITE_DEFAULT_RESTAURANT_SLUG`) — achado comparando com `grep -r VITE_
  apps/*/src`.
* **Novo `docs/deploy/railway_setup.md`**: guia completo pro painel da
  Railway (plugins gerenciados, Shared Variables, tabela de
  variáveis/healthcheck por serviço, ordem recomendada do primeiro
  deploy) — não executável por mim (sem acesso ao painel), preparado pro
  usuário aplicar manualmente. `infrastructure_strategy.md` atualizado
  (seção CI/CD) pra refletir Railway em vez do deploy manual via SSH
  descrito antes.

### Adicionado — Sistema de design estendido: Faturamento + apps Flutter
* **`admin-web` Faturamento**: os 3 KPIs (Faturamento Total, Taxa de
  Serviço, Comandas Fechadas) agora usam o componente `StatTile` real em
  vez de blocos repetidos manualmente; `PaymentHistoryTable` com os tokens
  novos e fonte de dado tabular na coluna de valor.
* **`waiter-mobile`/`customer-mobile`**: `AppTheme` dos dois apps portado
  pra `ColorScheme`/`TextTheme` com a mesma paleta dos apps web (sem
  arquivo de fonte pra embutir — pilhas/pesos do sistema, mesmo
  raciocínio já usado na web). `waiter-mobile` é interno, paleta fixa;
  `customer-mobile` já tinha um hook de White-Label (`AppTheme.light({Color?
  primary})`, `colorFromHex()`) que existia desde a criação do app mas
  **nunca era chamado com uma cor real** — `CustomerApp` virou
  `ConsumerWidget` e agora aplica a cor de marca do tenant (`restaurantProvider`)
  no `MaterialApp` raiz assim que carrega, propagando pra todas as rotas
  (`MenuScreen`/`ProductDetailScreen`), não só a tela onde o dado chegou.
* **Verificação**: `flutter analyze` limpo nos dois apps Flutter;
  `flutter test` sem regressão (`waiter-mobile` 20/20, `customer-mobile`
  com 2 testes novos provando a troca de tema ao vivo — antes do
  restaurante carregar usa o acento padrão, depois usa a cor real vinda
  da API). `admin-web`: `tsc`/`build`/`vitest` limpos, verificado ao vivo
  no dev server real.

### Adicionado — Sistema de design (admin-web + customer-web)
* Primeira direção visual real dos dois frontends — nenhum dos dois tinha
  `tailwind.config.js` além do boilerplate. Pitch aprovado antes de
  qualquer código (artifact com mockups das 3 telas), depois implementado.
* Tokens novos em `tailwind.config.js` dos dois apps: `ink`/`paper`/
  `surface`/`border` (neutros), `good`/`warning`/`critical` (estado
  semântico, fixo — nunca reaproveitado como acento), `accent` (marca).
  `admin-web` é ferramenta interna sem White-Label — paleta fixa. Em
  `customer-web`, `accent`/`paper`/`surface` **referenciam** as variáveis
  CSS do White-Label já existente (`--brand-primary`/`--brand-bg`/
  `--brand-surface`, `src/theme/branding.ts`) em vez de duplicá-las —
  continuam customizáveis por tenant, só o texto/borda/estado é fixo.
  3 famílias de fonte por papel (`display` geométrica pra telas
  operacionais lidas sob pressão, `menu` serifa itálica só no cardápio do
  cliente — a única leitura por prazer —, `data` monoespaçada pra
  números/dinheiro/tempo com `tabular-nums`).
* **`StatusBadge`** (novo componente `admin-web`, faixa lateral + pill com
  ponto colorido — nunca só cor): mapa de mesas ganhou 4 tons distintos
  (`good`=livre, `info`=reservada, `accent`=ocupada, `warning`=aguardando
  limpeza) — antes usava vermelho pra "ocupada" (uso normal da mesa, não
  problema), competindo visualmente com estados que realmente são
  urgentes.
* **KDS**: nova categoria **atrasado** (`critical`, faixa vermelha) pra
  itens `PENDING`/`PREPARING` parados ≥10min (reaproveita o limiar que já
  existia isolado em `ElapsedTime`, agora exportado como
  `getElapsedUrgency`) — antes um item atrasado 40min parecia idêntico a
  um de 2min.
* **Dashboard**: última barra do gráfico mensal (mês corrente) ganha o
  acento de marca + destaque, o resto fica com opacidade reduzida — antes
  o número que mais importa não se distinguia dos outros cinco.
  `StatTile` ganhou fonte de dado tabular pro valor.
* **Cardápio digital**: nome do prato em serifa itálica (`ProductCard`),
  preço com fonte de dado + acento de marca.
* **Verificação**: `tsc --noEmit`/`npm run build`/`vitest` limpos nos dois
  apps (`admin-web` 17/17, novos testes de `StatusBadge`/`getElapsedUrgency`;
  `customer-web` sem regressão nova, mesma falha pré-existente de sempre).
  Verificado ao vivo contra os dois dev servers reais — achado e corrigido
  no caminho: mudança em `tailwind.config.js` não é pega só com `--reload`/HMR
  do Vite, precisou reiniciar os dois processos (mesmo tipo de pitfall já
  visto com `uv.lock`/Docker nesta sessão, agora do lado do frontend).

### Adicionado — Rate limiting nas rotas públicas (docs/SECURITY.md §2.7)
* Fecha a lacuna documentada desde sempre em `docs/SECURITY.md`
  ("endpoints de API pública: máx 100 req/min por tenant, Nginx zona
  `api_general` — ainda não replicado na aplicação"): mesmo
  `RedisRateLimiter` do rate limit de login, agora protegendo as rotas
  realmente públicas/anônimas (autoatendimento do cliente via QR Code +
  bootstrap de tenant) em 4 serviços — tráfego autenticado da equipe
  (KDS, dashboard, mapa de mesas) fica deliberadamente de fora.
* **`restaurant_security.rate_limiter`** (novo, pacote compartilhado):
  `RedisRateLimiter`/`InMemoryRateLimiter` promovidos de `auth-service`
  (onde nasceram) pra cá, mais `resolve_rate_limit_key()` — chave por
  `tenant_id` (via `TenantContextMiddleware`) quando resolvível, cai pro
  IP do cliente quando não há tenant ainda (bootstrap de restaurante).
  `auth-service` atualizado para importar do pacote em vez da cópia local.
* **`dining-service`** (3 rotas): `qr-secret/validate`, `open-command`,
  `customer-close`.
* **`menu-service`** (4 rotas): `GET /categories`, `/products`,
  `/products/{id}`, `/products/{id}/addon-groups`.
* **`payment-service`** (1 rota): `customer-checkout`.
* **`restaurant-service`** (3 rotas, chave por IP — nenhuma tem tenant
  resolvível): `POST /restaurants` (bootstrap), `GET /by-slug/{slug}`,
  `GET /{restaurant_id}`. Ganhou Redis pela primeira vez (`redis:
  RedisSettings`, cliente novo em `dependencies.py`) + `trust_proxy_headers`
  (mesmo padrão já usado no `auth-service`).
* Verificado ao vivo contra o Docker real: 101 requisições reais em
  `POST /restaurants` (as 100 primeiras `201`, a 101ª `429` RFC 7807);
  chave real no Redis inspecionada em cada serviço confirmando o
  particionamento por tenant/IP + path.

### Adicionado — Testes E2E Playwright
* **`tests/e2e/`** (raiz do monorepo — novo `package.json`/`playwright.config.ts`
  lá, fora de `apps/*`, já que os specs dirigem mais de um frontend):
  dois fluxos reais de ponta a ponta contra o stack Docker vivo, cada um
  criando seu próprio tenant isolado via API antes de abrir o navegador
  (`tests/e2e/support/seedTenant.ts`, mesmo padrão de
  `tests/integration/test_full_platform_flow.py`) — não depende do seed de
  demonstração, que já ficou em estados inconsistentes entre sessões.
  * `admin-checkout.spec.ts`: login → mapa de mesas → comanda → "Fechar e
    Cobrar" → abre o próprio caixa → Pix.
  * `customer-checkout.spec.ts`: autoatendimento do cliente com secret de
    QR Code real → "Fechar minha conta" → Pix → confirma via API que o
    valor cobrado bateu com o total real da comanda — protege
    especificamente o fluxo do bug crítico corrigido nesta mesma sessão.

### Corrigido — revisão de segurança manual (sem `/security-review`, repo ainda sem git)
* **Crítico — `POST /payments/customer-checkout` confiava cegamente no
  cliente**: `order_id`/`command_id`/`expected_total` eram aceitos direto
  do corpo da requisição pública (US-05.4), sem cruzar com o valor real da
  comanda — qualquer cliente com a própria secret de mesa válida podia
  interceptar a requisição e pagar um valor arbitrário, ou vincular o
  pagamento à comanda de outra mesa. Corrigido: o servidor agora descobre a
  comanda aberta de verdade (`dining-service`) e computa o total real
  (`order-service` + `restaurant-service`, taxa de serviço) sozinho —
  `CustomerCheckoutRequest` perdeu os 3 campos, viraram erro `422`
  (`extra_forbidden`) se enviados. Novos clients HTTP em `payment-service`:
  `HttpxOrderServiceClient`, `HttpxRestaurantServiceClient` (mesmo padrão
  do `HttpxDiningServiceClient` já existente); `HttpxDiningServiceClient`
  passou a chamar `open-command` (devolve a comanda real) em vez de só
  validar a secret. Endpoint da equipe (`POST /payments`) ganhou um piso de
  segurança equivalente (`StaffCheckoutUseCase`): rejeita `expected_total`
  menor que o total real dos pedidos da comanda — não confere a taxa de
  serviço com a mesma precisão (gap residual, mitigado por RBAC+JWT+auditoria,
  ver docs/logs/2026-08-10.md).
* **Alto — rate limiter de login colapsava pra um IP só atrás do Nginx de
  produção**: `request.client.host` sempre seria o IP do container Nginx
  pra todo mundo (nenhum serviço lia `X-Forwarded-For`), virando "5
  tentativas pro sistema inteiro" em vez de por usuário real. Corrigido com
  `trust_proxy_headers` (só `true` em produção, setado no
  `docker-compose.prod.yml` — o `auth-service` lá só é alcançável via o
  gateway) usando o **último** valor de `X-Forwarded-For` (o único que o
  Nginx garante não ter sido forjado pelo cliente).
* **Médio — nenhum checkout mandava `Idempotency-Key`**: retry de rede
  podia duplicar o `Payment`. `admin-web` e `customer-web` agora geram uma
  chave por sessão de modal (reaproveitada em retries, nova a cada
  abertura) e mandam no header — o `payment-service` já suportava isso
  desde US-05.2, só nunca tinha sido usado por nenhum cliente real.

### Adicionado
* **Rate limiting em `/login` e `/login-pin`** (`auth-service`, docs/SECURITY.md §2.7):
  máx 5 tentativas por minuto por IP, cada rota com balde próprio (esgotar
  uma não bloqueia a outra). Implementado sobre Redis (`RedisRateLimiter`,
  janela fixa via `INCR`+`EXPIRE`) em vez de uma lib nova (`slowapi`/`limits`)
  — o Redis já é dependência do serviço (blacklist de token) e o algoritmo
  cabia em poucas linhas. Excedeu o limite → `429` em formato RFC 7807
  (`RATE_LIMIT_EXCEEDED`). Descoberto durante a implementação: já existia
  uma zona de rate limit no Nginx de **produção** (`api_auth`, `5r/m`),
  mas genérica pro path `/api/v1/auth/*` inteiro e ausente do
  `docker-compose.dev.yml` — a proteção nova cobre qualquer ambiente,
  coexistindo com o Nginx em prod (defense in depth, não substituição).
* **Refatoração "Payment por Comanda"**: `Payment` ganha `command_id`
  (opcional, aditivo — nova migration `0004`), a referência autoritativa de
  "a qual comanda este pagamento pertence". Antes, uma comanda com vários
  pedidos usava **o primeiro pedido como referência** (`order_id`), que
  continua existindo por compatibilidade mas deixa de ser a fonte de
  verdade quando `command_id` está presente. `CheckoutModal.tsx`
  (`admin-web`) e `CustomerCheckoutModal.tsx` (`customer-web`) já mandam
  `command_id: command.id` no pagamento — nenhum dos dois precisou de
  mudança de props/fluxo, só do payload enviado. `useRevenue.ts`
  (`admin-web`) resolve a mesa do histórico de pagamentos via `command_id`
  quando presente, com fallback pra `order_id` em registros antigos (sem
  quebrar nada já gravado). Novo `GET /payments?command_id=` no
  `payment-service`, paralelo ao `?status=` já existente.
* **Cliente paga a própria comanda pelo `customer-web`** (US-05.4): botão "Fechar minha conta" no painel "Meu Pedido", disponível assim que há pedidos lançados na mesa (não depende de nenhuma ação do garçom) — Cartão ou Pix simulados, sem etapa de assinatura (fazia sentido só como evidência de conferência presencial do garçom, não se aplica a um pagamento autoatendido). Continua **complementar** ao fluxo do garçom com a maquininha no `admin-web`, não o substitui — "quem chegar primeiro" fecha a comanda.
  * `services/dining-service`: `GET /tables/{table_number}/open-command` e `POST /commands/{command_id}/customer-close` (ambas públicas, `X-Tenant-Id` + secret de QR Code da mesa em vez de papel de equipe) — dão ao `customer-web` o `command_id`/`service_fee_charged` e o encerramento da comanda sem JWT.
  * `services/payment-service`: `Payment.cash_register_id` vira opcional (migration `0003`) — pagamento remoto não tem operador/caixa físico por trás; dinheiro continua proibido nesse canal (rejeitado no use case mesmo que alguém tente forçar). Novo `POST /payments/customer-checkout` (público), autorizado validando a secret da mesa via uma chamada REST síncrona ao `dining-service` (`HttpxDiningServiceClient`) — primeira comunicação síncrona entre dois microsserviços deste projeto (`docs/ai/architecture.md` já permitia, só nunca tinha sido necessária até agora).
  * `apps/customer-web`: novo `CustomerCheckoutModal` (+ `CustomerCardForm`, `CustomerPixPanel`, ambos portados dos equivalentes do `admin-web` sem o bloco de assinatura), `useOpenCommand`/`useSubmitCustomerCheckout`. Ao concluir, a mesa é liberada (`WAITING_CLEANING`) e o painel mostra uma tela de agradecimento em vez de deixar o polling de pedidos falhar contra a secret já rotacionada.

### Corrigido
* `services/dining-service`: `Table.is_qr_secret_valid()` quebrava com `TypeError: can't compare offset-naive and offset-aware datetimes` quando `qr_secret_expires_at` vinha do banco sem timezone (reproduzido via SQLite nos testes de integração leves — Postgres/asyncpg em produção não tem esse problema). Normaliza pra UTC antes de comparar; achado escrevendo os testes de integração das duas rotas novas acima.
* **`payment-service` não subia no Docker** (`ModuleNotFoundError: No module named 'httpx'`): a dependência nova tinha sido adicionada ao `pyproject.toml` do serviço, mas o `uv.lock` da raiz do workspace nunca foi regenerado — a imagem instala via `uv sync --frozen` contra esse lockfile. Corrigido com `uv lock` + rebuild da imagem; só apareceu na verificação manual contra o stack Docker real (não é algo que testes locais via `uv run pytest` detectam, já que rodam contra o venv do host, não a imagem).
* Migration `0003` (`cash_register_id` nullable) aplicada manualmente contra o Postgres do `docker-compose.dev.yml` (`infra/scripts/migrate.sh payment-service`) — só tinha sido testada via SQLite em memória até então.

---

## [Unreleased] — 2026-08-07

### Adicionado
* **Animações Rive** nos 4 frontends (`waiter-mobile`, `customer-mobile`, `admin-web`, `customer-web`): indicador de carregamento (`liquid_download.riv`) substituindo spinners genéricos em telas de login/mapa de mesas/cardápio/dashboard, e uma celebração de recompensa com data-binding (`rewards.riv`) ao enviar um pedido, fechar uma comanda paga, ou o pedido do cliente virar "Pronto". Assets são exemplos oficiais gratuitos do próprio Rive (licença MIT) — trocáveis por arte com a marca do restaurante sem mudar código, bastando manter o nome do arquivo. Sempre com fallback pra um spinner/ícone comum se a animação falhar.
* **`POST /tables/{table_id}/mark-cleaned`** (`dining-service`) + botão "Mesa Limpa" no `admin-web` / toque na mesa no `waiter-mobile`: libera uma mesa `WAITING_CLEANING` de volta pra `AVAILABLE` (US-03.5). Sem isso, toda comanda encerrada prendia a mesa pra sempre — a transição já existia no domínio, só nunca tinha ganhado endpoint.

### Corrigido
* **PIN login do `waiter-mobile`** dava um erro genérico ("recurso não encontrado") quando alguém digitava o `tenant_id` (UUID) no campo que pede o *slug* do restaurante — agora detecta esse 404 específico e explica a causa provável. Placeholder de exemplo errado no `customer-mobile` (`ex: burger-house`) corrigido pra bater com o slug real do seed (`restaurante-demo`).
* Removido um teste-modelo do `flutter create` (nunca substituído) em `waiter-mobile`/`customer-mobile` que fazia `flutter analyze` falhar.

---

## [Unreleased] — 2026-08-06

### Adicionado
* **Dashboard Completo do dono/gerente** (`apps/admin-web`, aba "Visão Geral & Vendas", OWNER/MANAGER — demais papéis continuam vendo o resumo enxuto anterior): pedidos hoje/no mês, ticket médio, mesas atendidas no dia, **tempo médio de atendimento por mesa** (`Command.opened_at → closed_at`, agora exposto na API), **SLA da cozinha** (`KDSItem.created_at → ready_at`, novos campos persistidos a cada transição de status — meta de 15min configurável em código), gráfico de pedidos por mês e valor em pedidos por mês (6 meses), ranking dos produtos mais pedidos. Sem serviço de BI dedicado: agregado no cliente combinando `order-service`+`dining-service`+`kitchen-service`, mesmo padrão já usado em `useRevenue`. Gráficos em SVG nativo (sem nova dependência), paleta categórica validada (skill de dataviz do Claude Code).
* `services/dining-service`: `CommandResponse` passa a expor `opened_at`/`closed_at` (existiam na entidade, nunca tinham ido para o contrato da API).
* `services/kitchen-service`: `KDSItem` ganha `ready_at`/`delivered_at`, preenchidos automaticamente por `transition_to()` — nova migration `0002`.

### Adicionado (rodada 2 da noite)
* **Formas de pagamento no fechamento de comanda** (`CheckoutModal`): antes só cartão de crédito era possível (hardcoded). Agora tem seletor Crédito/Débito/Pix/Dinheiro — Pix ganhou tela própria (QR + "copia e cola" simulados, sem gateway real) e Dinheiro ganhou cálculo de troco no cliente; nenhum dos dois pede assinatura (não faz sentido pra nenhum dos dois).
* **Histórico de Pagamentos** na aba Faturamento: tabela com data/hora, mesa, forma de pagamento e valor de cada pagamento aprovado, mais recente primeiro, com botão pra ver a **assinatura do cliente** capturada no pagamento por cartão (não existia nenhuma tela pra isso antes — a assinatura só ficava salva no banco, nunca era mostrada de volta).
* `services/payment-service`: `Payment.created_at` (existia na tabela via `TenantAwareModel`, nunca tinha sido exposto no domínio/API) — é a base da ordenação do histórico.

### Corrigido — tabelas presas em "Aguardando Limpeza" sem saída
Descoberto testando: `TableStatus.WAITING_CLEANING → AVAILABLE` é uma transição válida no domínio (`Table.transition_to`), mas nunca existiu nenhum endpoint pra acioná-la — depois de fechar algumas comandas de teste, as 5 mesas da demo ficaram permanentemente indisponíveis pra abrir uma nova comanda. Corrigido manualmente via SQL desta vez (ambiente de dev); registrado como `US-03.5` no backlog — vira um botão "Mesa limpa" no `admin-web` quando for priorizado.

### Corrigido — dois bugs relatados em produção (sessão da noite)
* **QR Code do cardápio digital expirando em ~90s enquanto o cliente ainda estava na mesa**: `Table.rotate_qr_secret()` agora só é chamada quando a comanda é encerrada (`CloseCommandUseCase`) — a secret vale por todo o ciclo de ocupação da mesa, não por um TTL curto (mantido em 24h só como rede de segurança). `TableQrModal` não re-rotaciona mais sozinho a cada 75s.
* **Garçom (`WAITER`) travado em "Fechar e Cobrar" com "Você não tem um caixa aberto"**: o `payment-service` nunca dava a `WAITER` acesso a nenhum endpoint de pagamento — nem para consultar se tinha caixa. Modela o fluxo real (garçom cobra na mesa com a própria maquininha): `WAITER` agora abre/consulta/fecha o **próprio** caixa e processa pagamento; auditoria mais ampla (qualquer caixa por ID, sangria/suprimento, listar todos os pagamentos) continua OWNER/MANAGER/CASHIER. `CheckoutModal` ganhou um botão real "Abrir meu caixa" (não existia nenhuma UI pra isso antes, pra nenhum papel).
* Ver `docs/logs/2026-08-06.md` (dev-brain) e `docs/TESTING_GUIDE.md` §7 para o diagnóstico completo e a verificação ao vivo contra o stack Docker resetado.

---

## [Unreleased] — 2026-08-05

### Adicionado & Testado
* **Backend — os 8 microsserviços Tier A completos** (`auth`, `restaurant`, `menu`, `dining` já entregues; `order`, `kitchen`, `inventory`, `payment` fechados nesta rodada), todos em Clean Architecture completa (domain/application/infrastructure/presentation), persistência real via SQLAlchemy 2.0 Async + Alembic, RFC 7807, isolamento de tenant, lock otimista, e testes unitários + integração (SQLite in-memory) 100% passando:
  * `order-service`: motor de pedidos com máquina de estados (`PENDING→PREPARING→READY→DELIVERED`), idempotência real via Redis, publica `order.created` para a Saga. 31 testes.
  * `kitchen-service`: KDS persistido (`KDSItem`/`KDSLog`), WebSocket com isolamento de tenant por token JWT na query string, consome `order.created` via RabbitMQ. 31 testes.
  * `inventory-service` (criado do zero): `InventoryItem`/`Supplier`/`Recipe`/`StockMovement`, movimentações manuais (entrada/perda/devolução) e contagem de inventário, baixa automática de insumos reagindo a `order.created` via ficha técnica. 40 testes.
  * `payment-service`: `CashRegister`/`CashMovement`/`Payment`/`PaymentSplit`, abertura/fechamento cego de caixa com relatório de divergência, split de pagamento entre meios, idempotência real via Redis. 41 testes.
* **Backend — os 4 microsserviços Tier B** (`delivery`, `marketing`, `notification`, `analytics`), base sólida sem integrações externas reais, mesma profundidade arquitetural dos Tier A em escopo reduzido:
  * `delivery-service`: `Delivery` com máquina de estados, ponto de extensão para iFood/Rappi (`ExternalDeliveryProviderInterface`, não implementado). 20 testes.
  * `marketing-service`: `Coupon` (desconto percentual/fixo, janela de validade, limite de usos). 26 testes.
  * `notification-service`: `NotificationTemplate`/`Notification`, publica `notification.requested` para a fila do Dramatiq via bridge dos workers. 19 testes.
  * `analytics-service`: `AuditLog` imutável consumindo **todo** evento de domínio via binding curinga `#` no exchange RabbitMQ compartilhado, consulta paginada (`PaginatedResponse[T]`). 13 testes.
* **`workers/`** (novo pacote do workspace, ADR-002): broker Dramatiq/Redis, actor `send_notification` (log estruturado no lugar de envio real de e-mail/WhatsApp/Push), actor + agendador APScheduler `generate_daily_sales_report`, bridge RabbitMQ→Dramatiq (`notification_bridge`) desacoplando a Saga do processamento em segundo plano. 5 testes.
* **`apps/admin-web`**: login real contra `auth-service` (Zustand + TanStack Query), mapa de mesas/KDS/branding conectados a dados reais (`dining-service`/`kitchen-service`/`restaurant-service`); adicionada fundação de build ausente (`tsconfig`, Tailwind/PostCSS, Vitest) — o app não compilava antes desta rodada. 11 testes Vitest, build de produção limpo.
* **`apps/customer-web`**: `mock-menu-repository.ts` substituído por repositório HTTP real contra `menu-service`/`restaurant-service` (branding dinâmico por slug via `?r=`), removidos dados fabricados no cliente (nota/avaliações/preço "de-por" que o backend não expõe) e o botão de customização de tema (não fazia sentido no app do cliente). 11 testes Vitest, build de produção limpo.
* **`apps/waiter-mobile`** (Flutter, criado do zero — Tier A): Clean Architecture (domain/data/application/presentation) com Riverpod, login por PIN, mapa de mesas em tempo real, abertura de comanda, montagem de pedido e envio à cozinha via `order-service`. 20 testes (`flutter test`), `flutter analyze` limpo.
* **`apps/customer-mobile`** (Flutter, criado do zero — Tier B): skeleton navegável (seleção de restaurante por slug → cardápio real via `menu-service` → detalhe de produto), branding dinâmico. 12 testes (`flutter test`), `flutter analyze` limpo.
* **Verificação final de plataforma — subida real do stack completo, não só testes isolados**: `uv sync`/`ruff check .`/`ruff format --check .`/`mypy --strict` limpos em todo o workspace (18 membros: 5 packages + 12 services + workers); suíte Pytest agregada (`infra/scripts/test-all.sh`) com **100% de aprovação**; os 19 containers do `docker-compose.dev.yml` (Postgres, Redis, RabbitMQ, Meilisearch + 12 microsserviços + `dramatiq-worker`/`notification-bridge`/`scheduler`) sobem e ficam `healthy`; teste de integração real (`tests/integration/test_full_platform_flow.py`) passando contra o stack vivo, cobrindo criar restaurante → cadastrar dono → login → criar mesa → cadastrar produto → criar pedido → Saga popular o KDS → abrir caixa → pagar.
* `infra/scripts/dev-up.sh`/`.ps1` (novos): builda e sobe o stack dev completo com `--env-file .env.dev` (compose não carrega esse arquivo automaticamente por não se chamar `.env`), roda as migrations e imprime a URL de health-check de cada serviço. `infra/scripts/dev-down.sh`/`.ps1` (novos): encerram o stack com o mesmo `--env-file`. Adicionados depois que a tentativa manual do usuário (`docker compose ... up -d --build` sem `--env-file`) falhou com dezenas de "variable is not set" e `no port specified`.
* `infra/scripts/migrate.ps1` (novo): equivalente PowerShell do `migrate.sh` reescrito (ver "Corrigido" abaixo).

### Corrigido — bugs reais só detectáveis subindo o stack de ponta a ponta

Esta seção existe porque a verificação final (subir os 19 containers de verdade + rodar um teste de integração real contra RabbitMQ/Postgres reais) revelou bugs que nenhuma bateria de testes unitários/SQLite anterior conseguia detectar. É exatamente o cenário que a exigência "só pare quando estiver rodando e com testes" veio prevenir.

* **`packages/events/src/restaurant_events/bus.py` — bug crítico de fan-out da Saga**: `RabbitMQEventBus.subscribe()` sempre declarava a fila com o mesmo nome (`f"{routing_key}.queue"`), então quando `kitchen-service` e `inventory-service` assinavam `order.created` — dois serviços independentes que precisam **ambos** reagir ao mesmo evento — eles viravam consumidores concorrentes da **mesma** fila (round-robin do RabbitMQ), e não assinantes independentes. Só um dos dois recebia cada evento. Detectado porque o teste de integração ficou preso esperando o item aparecer no KDS; confirmado via `rabbitmqctl list_queues name messages consumers` mostrando 2 consumers na fila `order.created.queue`. Corrigido adicionando parâmetro `queue_name` explícito ao `EventBus.subscribe()` (cada assinante agora declara sua própria fila nomeada: `kitchen-service.order.created`, `inventory-service.order.created`, `analytics-service.audit`, `workers.notification.requested`), propagado aos 4 pontos de assinatura reais. Novo teste de regressão em `packages/events/tests/test_bus.py` garantindo que dois assinantes independentes recebem o mesmo evento.
* **`services/menu-service/alembic/`**: o diretório existia mas estava **vazio** (sem `env.py`, `script.py.mako`, `versions/`, nem `alembic.ini`) apesar do serviço constar como "completo" — os 25 testes do serviço só exercitavam a camada de aplicação via SQLite em memória, nunca tocavam Alembic/Postgres real. Só apareceu ao rodar as migrations reais contra o Postgres do compose dev. Scaffold completo criado, incluindo a migration inicial (`categories`/`products`/`addon_groups`) espelhando os modelos SQLAlchemy existentes.
* **`infra/scripts/migrate.sh` reescrito**: a versão anterior rodava `alembic upgrade head` direto do host sem setar nenhuma variável de ambiente — funcionava por acaso quando as migrations eram testadas de outras formas, mas falhava com `ValidationError` (`db.name`/`rabbitmq` obrigatórios) porque esses valores só existiam como `environment:` do container, nunca como env var solta no host. Reescrito para carregar `.env.dev`, mapear a variável de nome de banco/Redis por serviço, e sobrescrever `DB__HOST`/`REDIS__HOST`/`RABBITMQ__HOST` para `localhost` (os hostnames de rede Docker como `postgres-db` só resolvem de dentro da rede do compose).
* **12 `Dockerfile` de serviço — `HEALTHCHECK` apontando para path errado**: todos ainda tinham `CMD` batendo em `/health` (path dos `main.py` mockados originais), mas os routers reais expõem o health em paths prefixados e inconsistentes entre si (`/api/v1/<service>/health` no `auth-service`, `/api/v1/<service>/health/check` nos demais 11). Todos os 12 containers reportavam `unhealthy` mesmo respondendo corretamente a `curl` manual. Corrigido path a path.
* **Healthcheck do Meilisearch (`docker-compose.dev.yml`/`.prod.yml`)**: `wget --spider http://localhost:7700/health` falhava com "Connection refused" de dentro do próprio container, mesmo com o processo escutando em `0.0.0.0:7700` — `/etc/hosts` da imagem resolve `localhost` para `::1` (IPv6) primeiro e o Meilisearch só bind em IPv4. Corrigido para `http://127.0.0.1:7700/health` explícito. Como `menu-service` depende de `meilisearch: condition: service_healthy`, esse container `unhealthy` travava `menu-service` indefinidamente em `Created`.
* `infra/docker/docker-compose.dev.yml`/`.env.dev`: variáveis `WORKERS_REDIS_DB`/`VITE_DEFAULT_RESTAURANT_SLUG` ausentes do `.env.dev` real (só existiam no `.example`), causando substituição vazia de `${VAR}` no compose.
* `workers/pyproject.toml`: `dramatiq-worker` entrava em crash-loop (`--watch` requer o extra `watch` do Dramatiq, ausente da dependência declarada).
* `services/dining-service`, `services/restaurant-service`, `services/menu-service` (alembic/env.py recém-criado): imports fora de ordem (ruff `I001`) normalizados na varredura final `ruff check --fix .`/`ruff format .`; `pyproject.toml` raiz ganhou `extend-exclude` para os artefatos gerados de build do Flutter (`ios/Flutter/ephemeral`, `.dart_tool`), que não são código-fonte do time.

---

## [Unreleased] — 2026-08-04

### Corrigido
* `packages/database/src/session.py`: corrigido erro de sintaxe em `DatabaseManager.session()` (faltava `self`) que impedia o módulo de ser importado.
* `packages/database`: `generate_uuid7()` gerava na verdade um UUIDv4; agora implementa RFC 9562 (UUIDv7) de verdade em `restaurant_core.ids`.
* `packages/security`: `require_role()` não funcionava com FastAPI (parâmetro tratado como query em vez de sub-dependency) por causa de `from __future__ import annotations` quebrando a resolução de `Depends()` sobre uma closure — corrigido.
* `docs`: `ADR-001-modular-monolith-architecture.md` marcada como Superseded; `README.md`, `ai/architecture.md`, `ROADMAP.md`, `ADR-006` e `infra/k8s/menu-service-deployment.yaml` (typo `IFNotPresent`) alinhados com a arquitetura de microsserviços vigente.

### Adicionado & Testado
* **Fundação compartilhada (`packages/*`)**: reestruturados para layout `src/<pacote>/` instalável via `uv workspace`. Novos pacotes `restaurant-common` (settings base, RFC 7807, paginação) e `restaurant-events` (`DomainEvent` + `EventBus` sobre RabbitMQ). `restaurant-database` ganhou `GUID` (tipo UUID agnóstico de dialeto) e `SQLAlchemyRepository` genérico tenant-aware. 67 testes automatizados.
* **Infraestrutura dev/prod separada**: `infra/docker/docker-compose.dev.yml` (Postgres/Redis/RabbitMQ/Meilisearch em container) vs `docker-compose.prod.yml` (Postgres externo/gerenciado, nunca em container). Dockerfile `uv` multi-stage padronizado para os 12 microsserviços, gateway Nginx, `.env.dev.example`/`.env.prod.example`.
* **`auth-service`**: implementação completa em Clean Architecture (domain/application/infrastructure/presentation) com persistência real (SQLAlchemy 2.0 Async + Alembic), substituindo os endpoints 100% mockados anteriores. Cadastro de dono/funcionários, login por senha e por PIN, refresh token com rotação, RBAC. 40 testes (unitários + integração), validado também manualmente contra Postgres/Redis reais via Docker.
* **Microsserviços de Backend e Suíte de Testes Automatizados** (entregas anteriores, mantidas como histórico):
  * `order-service`: Motor de pedidos com máquina de estados validada (`PENDING` -> `PREPARING` -> `READY` -> `DELIVERED`), cálculo de totais acumulados e emissão de eventos para a Saga.
  * `payment-service`: Controle do caixa operacional (abertura, suprimento, sangria com validação de saldo excedente, vendas) e recebimentos com garantia de idempotência.
  * Suíte de testes Pytest completa criada e executada com **100% de aprovação (12/12 testes passando)** em `auth-service`, `restaurant-service`, `menu-service`, `order-service` e `payment-service` (nota: esses testes iniciais cobriam apenas a camada de domínio; `auth-service` foi reescrito com camadas completas nesta rodada, conforme acima).
