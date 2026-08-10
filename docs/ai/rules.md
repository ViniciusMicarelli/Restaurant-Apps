# 📜 Regras Inegociáveis do Projeto para IAs

1. **NUNCA ESCREVER CÓDIGO SEM TESTES**:
   * Qualquer funcionalidade nova deve vir acompanhada dos seus respectivos testes automatizados em Pytest, Vitest ou Flutter Test.
2. **NUNCA IGNORAR FALHAS DE SEGURANÇA**:
   * Jamais contornar verificações de autorização, autenticação ou tenant scoping.
3. **PRESERVAR O LOG DE MUDANÇAS**:
   * Qualquer alteração relevante feita pela IA deve ser documentada no arquivo `docs/logs/YYYY-MM-DD.md` e em `docs/CHANGELOG.md`.
4. **MANTER COMPATIBILIDADE DE TIPOS**:
   * O código gerado deve passar 100% no `mypy --strict` e `ruff check`.
