# 🎨 Padrões de Projeto Permitidos e Proibidos para IA

## ✅ Padrões Obrigatórios / Recomendados

1. **Repository Pattern com Interfaces**:
   * Interfaces no `application/interfaces/repository_interface.py`.
   * Implementação concreta no `infrastructure/repositories/sqlalchemy_repository.py`.
2. **DTO (Data Transfer Object)**:
   * Schemas Pydantic v2 separados para Request, Response e Inter-Service.
3. **Use Case / Service Pattern**:
   * Cada caso de uso é uma classe única contendo o método `execute(...)`.
4. **Optimistic Locking**:
   * Uso da coluna `version_id` em entidades de alta movimentação.
5. **RFC 7807 Exception Handler**:
   * Exceções customizadas convertidas em `ProblemDetails`.

---

## ❌ Padrões Proibidos (Anti-Patterns)

1. **Fat Controllers / Endpoints Poluídos**:
   * Endpoints no FastAPI devem apenas validar o DTO de entrada, invocar o UseCase correspondente e retornar a resposta. Proibida lógica de negócio direta em arquivos de rota.
2. **SQL em Concatenação de Strings**:
   * Jamais criar instrução SQL via interpolação de strings.
3. **Silenciamento de Exceções (`try / except: pass`)**:
   * Proibido ignorar ou encobrir erros silenciosamente.
4. **Utilizar IDs Sequenciais Numéricos**:
   * Usar exclusivamente `UUIDv7` como chave primária.
