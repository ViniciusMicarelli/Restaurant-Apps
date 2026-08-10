# ADR-002: Seleção de Gerenciador de Filas e Processamento Assíncrono (Dramatiq vs Celery)

* **Status**: Aprovado
* **Data**: 2026-08-04
* **Decisores**: Arquiteto de Software Sênior

---

## Contexto e Problema

O sistema exige o processamento de tarefas em segundo plano (*Background Jobs*), tais como:
1. Envio de notificações WhatsApp e e-mails de confirmação.
2. Geração de relatórios pesados em PDF/Excel.
3. Webhooks de integração com gateways de pagamento e iFood.
4. Processamento de fechamento automático de caixas e limpezas periódicas.

Precisamos definir a ferramenta padrão para filas de tarefas em Python entre **Celery** e **Dramatiq**.

---

## Opções Consideradas

1. **Celery**:
   * *Prós*: Padrão de mercado estabelecido há anos em Python, documentação vasta, grande quantidade de plugins.
   * *Contras*: Configuração extremamente complexa, API legada com comportamento imprevisível em ambientes assíncronos (`asyncio`), alto consumo de memória dos workers, problemas históricos de perda de tarefas com backend Redis se não configurado perfeitamente.
2. **Dramatiq**:
   * *Prós*: Projetado especificamente para sistemas modernos Python 3.x; API extremamente limpa e intuitiva; suporte de primeira classe a retentativas com backoff exponencial; resiliência contra vazamento de memória e perda de mensagens; integração nativa com Redis e RabbitMQ.
   * *Contras*: Ecossistema ligeiramente menor que o Celery.

---

## Decisão

Decidimos adotar o **Dramatiq** com **Redis** como Message Broker padrão.

---

## Consequências

* **Simplicidade de código**: Declaração de tarefas limpa com decorador `@dramatiq.actor`.
* **Alta Concorrência**: Desempenho superior e menor consumo de recursos de CPU/Memória nos contêineres de workers.
* **Segurança e Confiabilidade**: Retentativas e dead-letter queues nativas configuradas sem hacks adicionais.
