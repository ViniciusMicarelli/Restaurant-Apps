# 🧪 Estratégia de Testes

> Complementa a regra inegociável #1 de [`docs/ai/rules.md`](../ai/rules.md) ("NUNCA
> ESCREVER CÓDIGO SEM TESTES"). Fecha a lacuna apontada na auditoria de 2026-08-04
> (link presente no índice do README sem conteúdo correspondente).

## Pirâmide de testes do projeto

| Nível | Local | Ferramenta | O que cobre | Depende de infra externa? |
|---|---|---|---|---|
| Unitário (domínio) | `services/<x>/tests/unit/` | Pytest | Entidades, Value Objects, máquinas de estado | Não |
| Unitário (caso de uso) | `services/<x>/tests/unit/` | Pytest + repositório fake | Use cases contra a interface do repositório (não a implementação) | Não |
| Unitário (pacotes) | `packages/*/tests/` | Pytest (+ SQLite em memória para `restaurant_database`) | Hash/JWT, exceções, repositório genérico, EventBus | Não |
| Integração | `services/<x>/tests/integration/` | Pytest + Postgres real | Repositório SQLAlchemy real, migrations Alembic | Sim (Postgres do `docker-compose.dev.yml`) |
| Integração entre serviços | `tests/integration/` (raiz) | Pytest + `httpx.AsyncClient` | Fluxos que atravessam >1 microsserviço (Saga) | Sim (stack `docker-compose.dev.yml` de pé) |
| E2E | `tests/e2e/` (raiz) | Playwright | Fluxo de usuário real no `admin-web` **e** no `customer-web` (checkout do garçom e autoatendimento do cliente) | Sim (stack completa + os dois frontends rodando) |
| Frontend (unit/component) | `apps/*/src/**/*.test.ts(x)` | Vitest | Hooks, componentes, repositórios HTTP | Não (mocka `fetch`) |
| Mobile | `apps/*-mobile/test/` | `flutter test` | Lógica de carrinho/pedido, parsing de API | Não |

## Convenções

- Testes de integração que exigem Postgres real usam uma fixture que tenta
  conectar e faz `pytest.skip("Postgres indisponível")` se a conexão falhar
  — nunca travam a suíte inteira quando ninguém subiu o `docker-compose.dev.yml`.
- `SQLAlchemyRepository` genérico (`packages/database`) é testado uma única
  vez contra SQLite em memória; os repositórios concretos de cada serviço só
  precisam de testes de integração para as queries específicas que
  adicionarem além do CRUD herdado.
- Nenhum teste depende de ordem de execução ou de estado deixado por outro
  teste (cada teste cria seus próprios dados/tenant via fixtures).
- Mutation testing (citado no `README.md`) não está configurado ainda —
  nenhuma ferramenta (`mutmut`/`cosmic-ray`) foi adotada; tratado como débito
  técnico aberto para uma fase futura, não uma exigência ativa hoje.

## Comando único por serviço/pacote

Cada `services/<x>/` e `packages/<x>/` roda de forma independente:

```bash
cd services/order-service && uv run pytest -q
```

`infra/scripts/test-all.*` percorre todos os diretórios com `pyproject.toml`
e executa `uv run pytest` em cada um, agregando o resultado — é o comando
usado em CI e antes de qualquer PR (`CONTRIBUTING.md`).

## E2E (Playwright) — `tests/e2e/`

`package.json`/`playwright.config.ts` vivem na **raiz** do monorepo (não
dentro de `apps/*` — os specs dirigem mais de um frontend no mesmo teste).
Cada spec cria seu próprio tenant isolado via API antes de abrir o
navegador (`tests/e2e/support/seedTenant.ts`, mesmo padrão de
`tests/integration/test_full_platform_flow.py`) — não depende do seed de
demonstração (`infra/scripts/seed_demo_data.py`), que já ficou em estados
inconsistentes entre sessões de teste manual.

```bash
# Pré-requisito: stack Docker + admin-web (:3001) + customer-web (:3000) já
# rodando — infra/scripts/dev-up.ps1 + apps-up.ps1 (ver TESTING_GUIDE.md).
npm install                        # uma vez, instala @playwright/test
npx playwright install chromium    # uma vez, baixa o engine
npx playwright test                # roda os specs de tests/e2e/
```
