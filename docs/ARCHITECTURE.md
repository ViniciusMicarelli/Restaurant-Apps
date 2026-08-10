# 🏛️ Documento de Arquitetura de Software — Restaurant Apps Platform

## 1. Visão Geral da Arquitetura: Microsserviços Distribuídos

A **Restaurant Apps Platform** adota uma **Arquitetura de Microsserviços Distribuídos Orientada a Eventos (Event-Driven Microservices)** com princípios de **Clean Architecture** e **Domain-Driven Design (DDD)**.

### Fundamentos da Escolha
1. **Desacoplamento Absoluto**: Cada microsserviço reside em seu próprio diretório sob `services/`, possui seu próprio ciclo de vida, banco de dados isolado (Database-per-Service ou Schema-per-Service) e pipeline de deploy.
2. **Escala Horizontal Seletiva**: Módulos de altíssima exigência em horários de pico (ex: `order-service` e `kitchen-service`) podem escalar para dezenas de instâncias enquanto microsserviços de menor tráfego (ex: `analytics-service` ou `marketing-service`) consomem recursos mínimos.
3. **Resiliência e Tolerância a Falhas**: A indisponibilidade de um serviço secundário (ex: notificações ou geração de relatórios) não interrompe o lançamento de pedidos nas mesas nem a operação do caixa.
4. **Construção do Zero sem Pressa**: Permite focar na engenharia perfeita de cada microsserviço, padronizando ferramentas modernas de alta performance como o `uv` e `Meilisearch`.

---

## 2. Estrutura do Monorepo de Microsserviços

```
restaurant-apps/
├── services/                    # Microsserviços Autônomos (FastAPI + Python 3.12)
│   ├── auth-service/            # Autenticação, Usuários, Roles, RBAC/ABAC & PINs
│   ├── restaurant-service/      # Gestão de Restaurantes, Multi-tenancy & Configurações
│   ├── menu-service/            # Cardápio, Categorias, Produtos, Combos & Meilisearch (FTS)
│   ├── dining-service/          # Mesas, Comandas, Fila de Espera Virtual & Reservas
│   ├── order-service/           # Motor de Pedidos & Orquestrador de Sagas Distribuídas
│   ├── kitchen-service/         # Kitchen Display System (KDS), WebSocket & Impressão
│   ├── inventory-service/       # Estoque, Ficha Técnica & Baixa Automática de Insumos
│   ├── payment-service/         # Checkout, Abertura/Fechamento de Caixa, Split & Pix
│   ├── delivery-service/        # Integração iFood/Rappi, Logística de Entregadores
│   ├── marketing-service/       # Cupons de Desconto & Programa de Fidelidade
│   ├── notification-service/    # Worker & Disparador Push, WhatsApp Bot, E-mail
│   └── analytics-service/       # Relatórios BI, DRE Operacional & Audit Log Imutável
│
├── apps/                        # Clientes / Interfaces de Usuário
│   ├── admin-web/               # Painel Administrativo / POS (React + TS + Vite)
│   ├── customer-web/            # Web App Autoatendimento / Cardápio QR Code (React + Vite)
│   ├── waiter-mobile/           # App Mobile do Garçom (Flutter)
│   └── customer-mobile/         # App Mobile do Cliente (Flutter)
│
├── packages/                    # Pacotes e Bibliotecas Compartilhadas
│   ├── core/                    # Interfaces base, tipos primitivos, exceções globais
│   ├── database/                # Session Manager, Base Repository, Mixins Alembic
│   ├── security/                # Criptografia, Token JWT, Middlewares RLS/Tenant
│   ├── events/                  # Envelope de Eventos Distribuídos (EventBus / RabbitMQ)
│   └── common/                  # DTOs compartilhados, Pydantic Base Settings
│
├── workers/                     # Processadores Assíncronos Globais (Dramatiq Actors)
├── infra/                       # Infraestrutura como Código
│   ├── docker/                  # Dockerfiles com uv multi-stage & docker-compose.yml
│   ├── api-gateway/             # Configurações do Nginx / Kong / Traefik Gateway
│   ├── meilisearch/             # Configurações do motor de Busca Inteligente
│   └── monitoring/              # Prometheus, Grafana, OpenTelemetry Collector
│
└── docs/                        # Documentação Técnica e Arquitetural Completa
```

---

## 3. Padrão Interno de Cada Microsserviço (Clean Architecture)

Cada microsserviço em `services/<service_name>` segue a estrutura em 4 camadas:

```
services/menu-service/
├── pyproject.toml               # Dependências do serviço geridas via `uv`
├── uv.lock                      # Trava determinística de dependências gerada pelo `uv`
├── Dockerfile                   # Build de contêiner em 2 estágios com `uv`
├── src/
│   ├── config.py                # Pydantic Settings com injeção de env do Docker
│   ├── domain/                  # Entidades puras, Value Objects, Exceções de Domínio
│   ├── application/             # Casos de Uso (Use Cases) e Interfaces de Repositório
│   ├── infrastructure/          # Repositórios SQLAlchemy 2.0 Async, Redis, Meilisearch client
│   └── presentation/            # Controllers FastAPI, Schemas Pydantic v2, Handlers
└── tests/                       # Testes de unidade e integração do serviço (Pytest)
```

---

## 4. Gerenciamento de Pacotes com `uv`

Todos os microsserviços Python utilizam o **`uv`** (escrito em Rust pela Astral) para o gerenciamento de dependências e ambientes virtuais:
* **Velocidade de Build**: Instalação e resolução de dependências até 100x mais rápida.
* **Workspace Monorepo**: `uv workspace` permite gerenciar o projeto raiz e os microsserviços de forma unificada.
* **Docker Multi-Stage**: Utilização do instalador compilado `ghcr.io/astral-sh/uv` mantendo o contêiner final em menos de 150MB.

---

## 5. Injeção de Configurações: `pydantic-settings` + `docker-compose.yml`

As configurações de runtime são validadas de forma tipo-segura pelo `pydantic-settings`:
* Mapeamento de structs aninhadas via delimitador `env_nested_delimiter="__"` (ex: `DB__HOST`, `DB__PORT`, `REDIS__URL`).
* O `docker-compose.yml` injeta as variáveis de ambiente explicitadas, que sobrepõem arquivos `.env`.
* Validação rigorosa na inicialização: Se uma variável obrigatória (como `JWT_SECRET_KEY` ou `DB__PASSWORD`) estiver ausente, o container falha no start exibindo uma mensagem de erro explícita.

---

## 6. Busca Inteligente & Full-Text Search (FTS)

Adotamos uma **Estratégia Híbrida de Busca**:
1. **Cardápio Digital & Autoatendimento (Customer-Facing)**:
   * Powered by **Meilisearch**.
   * Suporte a *search-as-you-type* em tempo real, **Typo Tolerance** (tolerância a erros de digitação em português) e destaque de termos.
2. **Busca Operacional de Backoffice (Garçom, Caixa, Estoque)**:
   * Powered por **PostgreSQL `pg_trgm` (Trigramas) + `tsvector` + `unaccent`**.
   * Consultas transacionais diretas nos microsserviços operacionais com velocidade de execução em milissegundos.
