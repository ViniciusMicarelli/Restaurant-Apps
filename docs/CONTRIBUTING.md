# 🤝 Guia de Contribuição — Restaurant Apps Platform

Agradecemos o seu interesse em contribuir para a **Restaurant Apps Platform**! Siga as diretrizes abaixo para manter o projeto organizado, seguro e com alta qualidade de código.

---

## 🛠️ Fluxo de Trabalho (Git Workflow)

1. **Feature Branches**:
   * Crie uma branch a partir da `main` com o padrão: `feature/<modulo>-<descricao-curta>` ou `fix/<modulo>-<descricao-curta>`.
   * Exemplo: `feature/orders-add-kds-filter` ou `fix/auth-jwt-refresh-expiration`.
2. **Commits**:
   * Siga o padrão **Conventional Commits** (veja `CODING_STANDARDS.md`).
3. **Pull Requests (PR)**:
   * Todo PR deve conter uma descrição clara das alterações, referência à issue ou US do Backlog e evidências de testes passando.
   * Exige aprovação de ao menos 1 revisor e validação 100% verde na pipeline de CI.

---

## 🧪 Requisitos de Qualidade para Aceite de Código

* **Testes Automatizados**: Nenhuma alteração deve ser enviada sem testes unitários ou de integração correspondentes.
* **Linting & Formatação**:
  * Backend Python: `ruff check .` e `mypy --strict .` sem erros.
  * Frontend React: `npm run lint` e `npm run type-check` sem erros.
  * Mobile Flutter: `flutter analyze` 100% limpo.
* **Segurança**: Nunca faça commit de segredos, tokens, senhas ou arquivos `.env`.
