# 📋 Índice de Decisões de Arquitetura (ADRs) — Restaurant Apps Platform

Este repositório registra todas as Decisões Arquiteturais Relevantes (Architectural Decision Records - ADRs) para transparência, auditabilidade e alinhamento do time.

---

## 📑 Lista de ADRs Registradas

| ID | Título | Data | Status | Sumário da Decisão |
|---|---|---|---|---|
| [ADR-001](decisions/ADR-001-microservices-architecture.md) | Adoção da Arquitetura de Microsserviços Distribuídos | 2026-08-04 | **Aprovado** | Optar por Microsserviços Event-Driven com Padrão Saga para desacoplamento total, escala individual e independência de deploy. |
| [ADR-002](decisions/ADR-002-async-queue-dramatiq-celery.md) | Seleção de Gerenciador de Filas e Async Workers | 2026-08-04 | **Aprovado** | Utilizar Dramatiq como gerenciador de filas padrão com Redis/RabbitMQ devido ao menor consumo de recursos e API moderna async. |
| [ADR-003](decisions/ADR-003-multi-tenancy-strategy.md) | Estratégia de Isolamento Multi-Tenancy (SaaS) | 2026-08-04 | **Aprovado** | Adotar a abordagem Database-per-Service / Schema-per-Service com isolamento de `tenant_id` via SQLAlchemy Event Listeners + PostgreSQL RLS. |
| [ADR-004](decisions/ADR-004-uv-package-manager.md) | Gerenciamento de Pacotes Python com `uv` | 2026-08-04 | **Aprovado** | Utilizar `uv` (desenvolvido em Rust) para resolução ultrarrápida de dependências e builds determinísticos de Docker. |
| [ADR-005](decisions/ADR-005-pydantic-settings-docker-env-injection.md) | Injeção de Variáveis no Pydantic Settings via Docker | 2026-08-04 | **Aprovado** | Padronizar a injeção via `docker-compose.yml` utilizando `env_nested_delimiter="__"` e validação tipo-segura de runtime. |
| [ADR-006](decisions/ADR-006-full-text-search-meilisearch-pgtrgm.md) | Estratégia de Busca Inteligente & Full-Text Search (FTS) | 2026-08-04 | **Aprovado** | Estratégia Híbrida: Meilisearch para o Cardápio Digital (search-as-you-type + typo tolerance) e Postgres `pg_trgm` / `tsvector` para backoffice operante. |
