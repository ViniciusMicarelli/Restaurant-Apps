# 💻 Convenções de Código e Guia de Estilo — Restaurant Apps Platform

## 1. Convenções de Código Backend (Python / FastAPI / Microsserviços)

### 1.1 Gerenciamento de Dependências com `uv`
* **Gerenciador Padrão**: `uv` (Astral). Proibido o uso de `pip` direto ou `poetry`.
* **Adicionar Dependência**: `uv add <package_name>` dentro da pasta do microsserviço.
* **Ambiente Virtual**: `uv venv` e `uv sync`.
* **Lockfile**: O arquivo `uv.lock` deve ser obrigatoriamente incluído nos commits Git.

### 1.2 Injeção de Configurações (`pydantic-settings`)
* Toda classe de configuração estende `BaseSettings`.
* Usar `env_nested_delimiter="__"` para mapeamento de variáveis do Docker.
* Proibido acessar `os.environ` diretamente no código da aplicação. Utilizar a instância global `settings`.

### 1.3 Estilo de Código Python
* **Linter & Formatter**: `ruff check .` e `ruff format .`.
* **Type Checker**: `mypy --strict .` sem exceções.
* **Asincronismo**: `async/await` obrigatório em rotas, repositórios e clientes HTTP (`httpx.AsyncClient`).

---

## 2. Convenções de Código Frontend Web (React / TypeScript)

### 2.1 Ferramentas e Estilo
* **Linter & Formatter**: `eslint` + `prettier`.
* **Gerenciamento de Estado**: **TanStack Query** (servidor/cache) e **Zustand** (UI global).

---

## 3. Convenções de Código Mobile (Flutter / Dart)

### 3.1 Estilo e Linter
* `flutter_lints`, `dart format`, Riverpod / BLoC com `freezed`.

---

## 4. Convenções de Mensagens de Commit (Conventional Commits)

Format: `<type>(<scope>): <short description>`

* `feat(menu-service)`: add Meilisearch FTS indexing handler
* `feat(order-service)`: implement Saga orchestrator for payment compensation
* `chore(deps)`: update uv lockfile for auth-service
