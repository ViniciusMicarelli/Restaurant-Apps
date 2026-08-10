# 🍽️ Restaurant Apps Platform — Documentação Principal

Bem-vindo à documentação oficial da **Restaurant Apps Platform**, uma plataforma SaaS de alta performance, escalável e segura para gestão completa de restaurantes, salão, comandas, cozinha (KDS), entregas, autoatendimento e inteligência de negócios.

---

## 📌 Índice da Documentação

### 1. Visão Geral e Arquitetura
* [📌 README Geral](README.md) — Este documento.
* [🏛️ Arquitetura do Sistema](ARCHITECTURE.md) — Visão geral da Arquitetura de Microsserviços Distribuídos Orientada a Eventos, DDD e padrões de design.
* [🏛️ Visão Detalhada de Arquitetura](architecture/system_overview.md) — Diagramas C4, fluxo de dados e isolamento entre serviços.
* [📋 Registro de Decisões de Arquitetura (ADR)](DECISIONS.md) — Índice de ADRs consolidadas.
  * [ADR-001: Microsserviços Distribuídos](decisions/ADR-001-microservices-architecture.md) (substitui a proposta original de Modular Monolith, preservada em [ADR-001-modular-monolith-architecture.md](decisions/ADR-001-modular-monolith-architecture.md) apenas como histórico)
  * [ADR-002: Seleção de Gerenciador de Filas e Tasks Async (Dramatiq)](decisions/ADR-002-async-queue-dramatiq-celery.md)
  * [ADR-003: Estratégia de Multi-Tenancy (Row-Level Isolation com `tenant_id`)](decisions/ADR-003-multi-tenancy-strategy.md)

### 2. Segurança e LGPD
* [🔒 Diretrizes de Segurança](SECURITY.md) — Defesas contra OWASP Top 10, IDOR, Race Conditions, RBAC/ABAC e Criptografia.
* [🛡️ Arquitetura Detalhada de Segurança](security/security_architecture.md) — Isolamento de Tenants, Gestão de Segredos, JWT/OAuth2 e Audit Log.

### 3. Banco de Dados e Dados
* [🛢️ Modelagem do Banco de Dados](DATABASE.md) — Modelagem ER, entidades principais, estratégias de locks e idempotência.
* [📊 Design de Schema](database/schema_design.md) — Mapeamento detalhado de tabelas, índices e particionamento.

### 4. APIs e Módulos
* [🔌 Guia de APIs](API_GUIDELINES.md) — Padrões OpenAPI/REST, convenções de versionamento, tratamento de erros e rate limiting.
* [🧩 Detalhamento de Módulos](modules/module_breakdown.md) — Módulos funcionais: Cardápio, Mesas, Comandas, Pedidos, KDS, Estoque, Pagamentos, etc.

### 5. Planejamento, Roadmap e Mudanças
* [🗺️ Roadmap Completo](ROADMAP.md) — Planejamento estratégico por fases (Fase 1 a Fase 5).
* [📋 Backlog do Projeto](BACKLOG.md) — Tarefas e épicos priorizados.
* [📝 Changelog](CHANGELOG.md) — Histórico de edições das versões do sistema.
* [📅 Diário de Modificações (Logs)](logs/2026-08-04.md) — Logs diários detalhados de evolução.

### 6. Engenharia, Desenvolvimento e Testes
* [💻 Padrões de Código](CODING_STANDARDS.md) — Guia de estilo para Python/FastAPI, React/TypeScript e Flutter/Dart.
* [🤝 Guia de Contribuição](CONTRIBUTING.md) — Fluxo de trabalho Git (GitFlow/Feature Branch), Code Review e Pull Requests.
* [🧪 Estratégia de Testes](testing/test_strategy.md) — Testes unitários, de integração, E2E e mutation testing.
* [🚀 Estratégia de Deploy e Infraestrutura](deploy/infrastructure_strategy.md) — Docker, CI/CD, Observabilidade (Logs, Metrics, Tracing).
* [🧪 Guia de Teste Manual](TESTING_GUIDE.md) — URLs de cada app/serviço, papéis RBAC por rota, credenciais do seeder de demonstração (§7 tem as correções da noite de 2026-08-06).

### 7. Guia para Agentes de Inteligência Artificial (AI Context)
* [🤖 AI Context Home](ai/context.md) — Contexto de entrada rápida para LLMs e assistentes de IA.
* [🧠 AI Architecture Guidelines](ai/architecture.md) — Regras de arquitetura e Clean Code para IA.
* [🎨 AI Design & Coding Patterns](ai/patterns.md) — Padrões de projeto permitidos e proibidos.
* [📜 AI System Rules](ai/rules.md) — Regras inegociáveis do projeto.
* [💬 AI Prompts](ai/prompts/prompt_templates.md) — Templates de prompts otimizados.

---

## 🛠️ Tech Stack Principal

| Camada | Tecnologias Utilizadas |
|---|---|
| **Backend API** | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, asyncpg |
| **Banco de Dados & Cache** | PostgreSQL 16+, Redis 7+ |
| **Async Workers & Tasks** | Dramatiq (ADR-002), Redis Broker |
| **Frontend Web Admin/POS** | React 19, TypeScript, Vite, TanStack Query, TailwindCSS, Zustand |
| **Mobile (Garçom / Cliente)** | Flutter 3.x, Dart, Riverpod / BLoC |
| **Infraestrutura & DevOps**| Docker, Docker Compose, Nginx, GitHub Actions, Prometheus, Grafana, OpenTelemetry |
| **Testes** | Pytest, pytest-asyncio, Vitest, Playwright, Flutter Test |
