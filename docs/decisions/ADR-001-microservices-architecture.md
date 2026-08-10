# ADR-001: Adoção da Arquitetura de Microsserviços Distribuídos

* **Status**: Aprovado (substitui [ADR-001-modular-monolith-architecture](ADR-001-modular-monolith-architecture.md), superseded no mesmo dia)
* **Data**: 2026-08-04
* **Decisores**: Arquiteto de Software Sênior & Visão de Longo Prazo do Projeto

---

## Contexto e Problema

O projeto **Restaurant Apps Platform** almeja ser construído do zero com foco em desacoplamento máximo, independência de implantação, escalabilidade individual por serviço e isolamento estrito de domínios operacionais. Como o projeto é construído sem urgência de prazo ("sem pressa"), podemos focar na construção da melhor engenharia distribuída possível desde o primeiro dia.

Precisamos definir a arquitetura de software para o backend da plataforma.

---

## Opções Consideradas

1. **Monólito Modular**:
   * *Prós*: Deploy simples, única aplicação.
   * *Contras*: Acoplamento em tempo de execução; todas as partes rodam na mesma instância de processo e dependem da mesma escala vertical.
2. **Microsserviços Distribuídos Event-Driven**:
   * *Prós*:
     * **Independência Total de Deploy**: Cada serviço (`auth`, `menu`, `orders`, `kitchen`, `payments`, etc.) possui seu próprio ciclo de vida, banco de dados (Database-per-Service ou Schema-per-Service) e pipeline CI/CD.
     * **Escalabilidade Granular**: Módulos de alta carga em horários de pico (ex: `orders` e `kitchen`) podem escalar horizontalmente para dezenas de réplicas sem gastar recursos com módulos de baixa carga (ex: `analytics` ou `marketing`).
     * **Resiliência e Tolerância a Falhas**: Uma falha no serviço de relatórios ou notificações não derruba a criação de pedidos no salão ou o KDS da cozinha.
     * **Isolamento Estrito de Código e Tecnologias**: Sem vazamento de entidades ou dependências entre módulos.
   * *Contras*: Necessidade de orquestração de transações distribuídas (Padrão Saga), gestão de API Gateway, service discovery e tracing distribuído com OpenTelemetry.

---

## Decisão

Decidimos adotar a **Arquitetura de Microsserviços Distribuídos Orientada a Eventos (Event-Driven Microservices)**.

---

## Estrutura de Comunicação e Transações

1. **Comunicação Síncrona**: Chamadas internas via gRPC ou HTTP/2 REST entre serviços protegidos por API Gateway (Kong / Traefik / Nginx).
2. **Comunicação Assíncrona**: Barramento de eventos distribuído via **RabbitMQ / Redis PubSub** para disparo de eventos de domínio (`OrderCreated`, `PaymentSettled`, `StockDepleted`).
3. **Transações Distribuídas (Padrão Saga)**:
   * Adoção de **Saga por Coreografia** para fluxos assíncronos desacoplados (ex: Pedido Criado -> Reserva Estoque -> Efetua Pagamento -> Dispara KDS).
   * Implementação de ações de compensação para rollback distribuído caso uma etapa falhe.
