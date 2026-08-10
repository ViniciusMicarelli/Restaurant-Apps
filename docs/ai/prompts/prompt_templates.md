# 💬 Prompt Templates para Colaboração com IA

## Template 1: Criação de Novo Módulo (Bounded Context)

```text
Você atua como Arquiteto de Software Sênior na Restaurant Apps Platform.
Preciso criar o módulo '<NOME_DO_MODULO>'.
Siga estritamente a Clean Architecture e DDD em Python/FastAPI:
1. Crie as entidades puras em domain/entities/.
2. Crie as interfaces de repositório em application/interfaces/.
3. Crie os DTOs Pydantic v2 em application/dtos/.
4. Crie os Casos de Uso (Use Cases) em application/use_cases/.
5. Crie a implementação do repositório SQLAlchemy 2.0 Async em infrastructure/repositories/.
6. Exponha os endpoints REST no FastAPI em presentation/api/.
Gere também a suíte de testes em Pytest com 100% de cobertura.
```

---

## Template 2: Revisão de Segurança de Endpoint

```text
Revise o endpoint '<ROTA>' considerando as diretrizes de SECURITY.md da Restaurant Apps Platform.
Verifique:
1. IDOR e Tenant Scoping (O tenant_id está sendo validado?).
2. Mass Assignment (O Pydantic schema impede campos extras?).
3. Rate Limiting e Roles RBAC.
4. Possibilidade de Race Conditions (Exige Optimistic ou Pessimistic Lock?).
```
