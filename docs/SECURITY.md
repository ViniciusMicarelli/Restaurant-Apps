# 🔒 Diretrizes de Segurança — Restaurant Apps Platform

## 1. Visão Geral da Estratégia de Segurança

A **Restaurant Apps Platform** adota a filosofia de **Defense in Depth (Defesa em Profundidade)** e **Zero Trust Architecture**. Em um sistema de gerenciamento financeiro, operacional e de pagamentos em tempo real para restaurantes, a segurança é prioridade absoluta.

---

## 2. Prevenção Contra Vulnerabilidades OWASP Top 10 e Ameaças Avançadas

### 2.1 IDOR (Insecure Direct Object References) & Broken Access Control
* **Mitigação**: NUNCA utilizar chaves primárias sequenciais numéricas simples (`1`, `2`, `3`) nas URLs ou payloads públicos. Todas as entidades usam **UUIDv7** ou **ULID**.
* **Tenant Scoping Mandatório**: Todas as consultas ao banco de dados exigem a validação conjunta do `tenant_id` do usuário autenticado e a permissão no recurso.
* **Exemplo de Verificação**: `WHERE order_id = :order_id AND tenant_id = :current_tenant_id`.

### 2.2 Race Conditions & TOCTOU (Time-of-Check to Time-of-Use)
* **Mitigação**:
  * Em operações críticas de estoque e fechamento de mesas/comandas, utilização de **Optimistic Locking** com coluna `version` em entidades SQLAlchemy.
  * Para movimentações de caixa e pagamentos simultâneos, utilização de **Pessimistic Locking** (`SELECT FOR UPDATE`) ou **Redis Distributed Locks (Redlock)** com TTL estrito.

### 2.3 SQL Injection, Command Injection & Path Traversal
* **SQL Injection**: Uso exclusivo de ORM (SQLAlchemy 2.0 Async) com queries parametrizadas. Proibição absoluta de concatenação direta de SQL puro.
* **Command Injection**: Proibição de chamadas `os.system()` ou `subprocess.Popen()` com entradas de usuários. Uso de APIs nativas em Python.
* **Path Traversal**: Validação e higienização estrita de nomes de arquivos enviados com `pathlib` e envio imediato para S3/MinIO com chaves geradas por hash (UUID), sem armazenar arquivos executáveis localmente.

### 2.4 Broken Authentication, Session Fixation & Replay Attacks
* **Senha e Hash**: Armazenamento com **Argon2id** (ou `bcrypt` com fator de custo elevado).
* **JWT**: Tokens de Acesso de curta duração (15 minutos) e Refresh Tokens de longa duração (7 dias) armazenados em cookies HTTP-Only, Secure, SameSite=Strict.
* **Replay Protection**: Assinatura JWT com `jti` (JWT ID) único registrado em Blacklist no Redis em caso de logout ou rotação.

### 2.5 Mass Assignment
* **Mitigação**: Uso rigoroso de Pydantic v2 Schemas com `extra="forbid"`. As rotas de criação e atualização usam DTOs explicitamente definidos, impedindo que campos sensíveis (como `is_superuser`, `tenant_id`, `role`) sejam injetados pelo cliente.

### 2.6 CSRF, XSS, SSRF & CORS
* **CSRF**: Proteção via cookies `SameSite=Strict` combinada com cabeçalho de verificação customizado (`X-Requested-With`) ou CSRF tokens para rotas mutation web.
* **XSS**: Sanitização automática no React/TypeScript, uso de Content Security Policy (CSP) severa via headers Nginx.
* **SSRF**: Validação de URLs fornecidas pelos usuários para Webhooks através de allowlists de domínios e bloqueio de IPs internos (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.169.254`).
* **CORS**: Origens restritas explicitamente por ambiente no FastAPI. Proibido o uso de `allow_origins=["*"]` em produção.

### 2.7 Rate Limiting & User Enumeration
* **Rate Limiting**:
  * Endpoints de Login (`POST /api/v1/auth/login`, `/login-pin`): máx 5
    tentativas por minuto por IP, implementado no `auth-service` sobre
    Redis (`INCR`+`EXPIRE`, janela fixa — `RedisRateLimiter`,
    `restaurant_security.rate_limiter` — pacote compartilhado desde que o
    mesmo padrão passou a proteger rotas públicas de outros serviços, ver
    abaixo; hand-rolled em vez de `limits`/`slowapi`, o algoritmo cabia em
    poucas linhas e o Redis já é dependência de praticamente todo
    serviço). Cada rota tem seu próprio balde por IP — esgotar `/login`
    não bloqueia `/login-pin`. 2026-08-10.
  * Endpoints de API pública (autoatendimento do cliente via QR Code +
    bootstrap de tenant): máx 100 req/min, mesmo `RedisRateLimiter`
    compartilhado, chave via `resolve_rate_limit_key` — por `tenant_id`
    quando resolvível (`dining-service`: `qr-secret/validate`,
    `open-command`, `customer-close`; `menu-service`: `GET
    /categories`/`/products`/`/products/{id}`/`/products/{id}/addon-groups`;
    `payment-service`: `customer-checkout`), cai pro IP do cliente quando
    não há tenant ainda (`restaurant-service`: `POST /restaurants`
    — bootstrap —, `GET /by-slug/{slug}`, `GET /{restaurant_id}`).
    Escopo deliberadamente restrito a rotas realmente anônimas — tráfego
    autenticado da equipe (KDS, dashboard, mapa de mesas) fica de fora:
    100/min já seria pouco pra uso normal de um turno inteiro de
    garçons/cozinha, e essas rotas não são as que um atacante sem
    credencial consegue bater. 2026-08-10.
  * Em **produção**, o Nginx do API Gateway (`infra/nginx/nginx.conf`,
    zona `api_auth`, `rate=5r/m`) aplica uma camada adicional genérica a
    todo `/api/v1/auth/*` — complementar à proteção da aplicação acima
    (defense in depth), não a única linha de defesa: o `docker-compose.dev.yml`
    não tem Nginx na frente, então a proteção real hoje é a do
    `auth-service` em si, válida em qualquer ambiente.
  * Endpoints de API pública: máx 100 requisições por minuto por tenant
    (Nginx, zona `api_general`) — replicado na aplicação em 2026-08-10,
    ver item acima.
* **Enumeração de Usuários**: Respostas genéricas em endpoints de autenticação e recuperação de senha (ex: "Se o e-mail existir no sistema, você receberá um link de recuperação").

---

## 3. Modelo de Autorização: RBAC + ABAC

A plataforma combina **RBAC (Role-Based Access Control)** e **ABAC (Attribute-Based Access Control)**:

* **Roles Padrão**:
  * `SUPER_ADMIN` (Gestor da Plataforma SaaS)
  * `RESTAURANT_OWNER` (Dono do Restaurante)
  * `MANAGER` (Gerente do Salão)
  * `CASHIER` (Operador de Caixa)
  * `WAITER` (Garçom)
  * `KITCHEN_STAFF` (Cozinheiro/KDS)
  * `CUSTOMER` (Cliente final)
* **Condições ABAC**:
  * Exemplo: Garçom só pode fechar uma comanda se for o responsável atribuído à mesa OU se tiver a permissão ABAC `override_waiter_lock`.
  * Exemplo: Cancelamento de item da cozinha exige autorização temporária com PIN do Gerente.

---

## 4. Log de Auditoria Imutável (Audit Trail)

Todas as ações críticas no sistema (alteração de preços, cancelamento de pedidos, sangria de caixa, concessão de descontos, alteração de permissões) geram registros imutáveis na tabela `audit_logs`:

| Campo | Descrição |
|---|---|
| `id` | UUIDv7 |
| `tenant_id` | Identificador do Restaurante |
| `actor_id` | ID do usuário que executou a ação |
| `action` | Ação (ex: `ORDER_ITEM_CANCELLED`, `PRICE_UPDATED`) |
| `resource_type` | Nome da entidade (ex: `OrderItem`) |
| `resource_id` | ID do recurso afetado |
| `old_values` | JSON contendo os dados anteriores |
| `new_values` | JSON contendo os novos dados |
| `ip_address` | IP do cliente |
| `user_agent` | Browser / App utilizado |
| `timestamp` | Data/hora exata em UTC com precisão de milissegundos |

---

## 5. Conformidade com a LGPD e Proteção de Dados

1. **Minimização de Dados**: Coleta estritamente do necessário para a prestação do serviço.
2. **Criptografia em Trânsito e Repouso**:
   * Em Trânsito: TLS 1.3 obrigatório para todas as comunicações.
   * Em Repouso: Criptografia AES-256 no PostgreSQL para campos sensíveis de clientes (CPF, Telefone, Cartão tokenizado).
3. **Direito ao Esquecimento (Right to be Forgotten)**:
   * Processo automatizado para anonimização de dados de clientes mediante solicitação, preservando apenas dados contábeis/fiscais exigidos por lei.
4. **Soft Delete e Imutabilidade Histórica**: Registros operacionais utilizam `deleted_at` com preservação para relatórios de auditoria.
