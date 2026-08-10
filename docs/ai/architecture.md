# 🧠 Regras Arquiteturais para Agentes de IA

Ao gerar código ou realizar refatorações neste projeto, qualquer agente de IA deve obedecer estritamente aos seguintes princípios:

1. **Respeitar as Fronteiras de Serviço (*Bounded Contexts*)**:
   * Proibido importar entidades ou repositórios internos de `services/auth-service` dentro de `services/order-service` (ou de qualquer outro serviço). Cada microsserviço é um processo e um deploy independentes (ADR-001-microservices-architecture).
   * Comunicações síncronas entre serviços ocorrem unicamente via API REST/gRPC; comunicações assíncronas ocorrem via eventos de domínio (`packages/events`, Saga por coreografia). Nenhum serviço acessa diretamente o banco de dados de outro (`docs/DATABASE.md`).
2. **Respeitar a Regra de Dependências da Clean Architecture**:
   * A camada `domain` NUNCA deve importar FastAPI, SQLAlchemy, Redis ou bibliotecas de infraestrutura.
   * Os dados chegam à camada de `domain` como Objetos de Valor (*Value Objects*) ou primitivos Python.
3. **Imutabilidade e Assincronismo**:
   * Todos os handlers de rota FastAPI e operações I/O devem ser assíncronos (`async def`).
   * Usar Pydantic v2 com `frozen=True` para DTOs e Value Objects sempre que aplicável.
4. **Isolamento de Tenant**:
   * Toda consulta SQL/SQLAlchemy deve explicitar a validação de `tenant_id`. NUNCA remover os filtros automáticos de tenant.
