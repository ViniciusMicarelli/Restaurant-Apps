# 🤖 Contexto Geral do Sistema para IAs — Restaurant Apps Platform

## Visão Geral para Agentes de Inteligência Artificial

Este repositório contém a **Restaurant Apps Platform**, uma plataforma SaaS de alta performance, escalável e segura para gestão operacional completa de restaurantes, salão, comandas, KDS da cozinha, estoques, pagamentos e delivery.

---

## 📌 Principais Referências de Documentação
* Arquitetura de Software: `docs/ARCHITECTURE.md`
* Segurança e Mitigações OWASP: `docs/SECURITY.md`
* Modelagem de Banco de Dados: `docs/DATABASE.md`
* Padrões de API e WebSockets: `docs/API_GUIDELINES.md`
* Guia de Estilo e Convenções: `docs/CODING_STANDARDS.md`
* Registro de Decisões (ADRs): `docs/DECISIONS.md` e `docs/decisions/*.md`

---

## 🧱 Resumo da Arquitetura do Backend
* **Python 3.12+ / FastAPI** em **Microsserviços Distribuídos Orientados a Eventos** (`services/`).
* **Gerenciamento de Pacotes**: `uv` (Astral) em todos os serviços.
* **Injeção de Configuração**: `pydantic-settings` via `docker-compose.yml` (`env_nested_delimiter="__"`).
* **Busca Inteligente (FTS)**: **Meilisearch** para Cardápio Digital (Typo tolerance) + **PostgreSQL `pg_trgm`** para Operações de Backoffice.
* **Transações Distribuídas**: **Padrão Saga por Coreografia** com RabbitMQ / Redis PubSub.
* **Clean Architecture + DDD**: Cada microsserviço isolado em `domain`, `application`, `infrastructure`, `presentation`.
* **Multi-tenancy**: Isolamento lógico obrigatório por `tenant_id` ativado via middleware no ORM e PostgreSQL RLS.
