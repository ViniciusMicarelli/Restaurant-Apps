# ADR-001: Adoção da Arquitetura Modular Monolith

* **Status**: ⚠️ **Superseded** por [ADR-001-microservices-architecture](ADR-001-microservices-architecture.md) em 2026-08-04
* **Data**: 2026-08-04
* **Decisores**: Arquiteto de Software Sênior & Equipe de Engenharia

> **Nota de revisão (2026-08-04)**: Esta ADR foi substituída no mesmo dia pela
> decisão registrada em `ADR-001-microservices-architecture.md`, que é a
> arquitetura efetivamente implementada (`services/*`, um banco por serviço,
> Saga por coreografia — ver `docs/ARCHITECTURE.md` e `docs/DECISIONS.md`).
> Este documento é mantido apenas como histórico da decisão original e do
> raciocínio que a motivou; não reflete o estado atual do sistema.

---

## Contexto e Problema

Estamos iniciando o desenvolvimento da **Restaurant Apps Platform**, um sistema SaaS abrangente para gestão de restaurantes. O sistema abrange múltiplos domínios funcionais complexos: Cardápio, Salão/Mesas, Comandas, Pedidos, Cozinha (KDS), Estoque, Pagamentos, Delivery e Notificações em tempo real.

Precisamos escolher o estilo arquitetural do backend Python/FastAPI considerando:
1. **Time-to-market e velocidade de desenvolvimento inicial**.
2. **Facilidade de implantação e operação de infraestrutura (DevOps)**.
3. **Manutenibilidade e isolamento de código**.
4. **Capacidade de evolução para Microserviços no futuro sem reescrita massiva de código**.

---

## Opções Consideradas

1. **Microserviços Distribuídos Tradicionais**:
   * *Prós*: Deploy independente de cada serviço; isolamento total de processo.
   * *Contras*: Alta complexidade de infraestrutura, distributed tracing obrigatório, latência de rede inter-serviços, consistência eventual complexa, alto custo de operação inicial.
2. **Monólito Tradicional Não Estruturado (Big Ball of Mud)**:
   * *Prós*: Extremamente simples no início.
   * *Contras*: Alto acoplamento, vazamento de regras de negócio entre módulos, acúmulo de débito técnico que inviabiliza o crescimento do sistema.
3. **Modular Monolith (Monólito Modular com Clean Architecture & DDD)**:
   * *Prós*: Processo de execução único no backend com isolamento estrito de módulos (*Bounded Contexts*). Comunicação direta em memória com tipagem estrita; facilidade de testes de integração; facilidade de extração futura de qualquer módulo para microserviço autônomo.
   * *Contras*: Exige disciplina rigorosa do time para não violar as fronteiras dos módulos.

---

## Decisão

Decidimos adotar a **Arquitetura Modular Monolith**.

Cada domínio funcional residirá sob `modules/<module_name>` contendo suas próprias camadas de Domain, Application, Infrastructure e Presentation.

As interações entre módulos síncronos ocorrerão exclusivamente por interfaces declaradas na camada de `application`. Interações assíncronas utilizarão um `EventBus` interno.

---

## Consequências

### Positivas
* Deploy simples via contêiner Docker único para a API.
* Desempenho máximo sem latência de rede RPC/HTTP entre serviços internos.
* Transações atômicas no banco de dados relacional quando estritamente necessário.
* Curva de aprendizado suave para novos desenvolvedores.

### Negativas / Riscos
* Risco de acoplamento indevido se desenvolvedores importarem componentes internos de outros módulos.
* *Mitigação*: Linter customizado/testes de arquitetura automatizados no CI (import linter) para bloquear importações diretas não autorizadas entre módulos.
