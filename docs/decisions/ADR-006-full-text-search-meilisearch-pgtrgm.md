# ADR-006: Estratégia de Busca Inteligente e Full-Text Search (FTS)

* **Status**: Aprovado
* **Data**: 2026-08-04
* **Decisores**: Arquiteto de Software Sênior

---

## Contexto e Problema

Uma experiência moderna de gerenciamento de restaurante e cardápio digital exige uma busca inteligente de alta performance. Os clientes e operadores realizam buscas complexas como:
1. **Clientes no Cardápio Digital (QR Code/App)**: Buscam por termos com erros de digitação (ex: "xeddar" em vez de "cheddar", "pisa" em vez de "pizza"), filtros por restrições alimentares ("sem glúten", "vegano") ou por tags/ingredientes.
2. **Operadores de Caixa e Garçons no POS/Salão**: Buscam em frações de segundo por número da comanda/mesa, código de pedido (`#1042`), nome ou telefone do cliente, ou itens do pedido.
3. **Gestores no Estoque e CRM**: Buscam por insumos, código de barras de fornecedor e histórico de consumo.

Precisamos definir a arquitetura e as tecnologias de **Full-Text Search (FTS)** para atender a esses casos de uso.

---

## Avaliação das Tecnologias

### 1. PostgreSQL Native FTS (`tsvector` / `tsquery`) + `pg_trgm` + `unaccent`
* **Prós**: Sem infraestrutura adicional (já utilizamos o PostgreSQL 16+ no microsserviço), transacional (ACID), busca trigrâmica eficiente para trechos de texto (`LIKE` de alta velocidade), isolamento multi-tenant nativo por `tenant_id`.
* **Contras**: Relevância de relevância avançada e *search-as-you-type* com tolerância extrema a erros exigem consultas SQL complexas.

### 2. Meilisearch
* **Prós**: Resposta ultra-rápida em milissegundos (< 20ms); suporte nativo a *search-as-you-type* (busca a cada caractere digitado); **Typo Tolerance** excepcional de fábrica (corrige letras trocadas, acentos e caracteres omitidos); busca facetada (por categoria, preço, alérgenos); leve no consumo de recursos.
* **Contras**: Requer sincronização assíncrona de índices a partir dos eventos de domínio do microsserviço de cardápio.

### 3. Elasticsearch / OpenSearch
* **Prós**: Altíssima capacidade de escala e busca vetorial/semântica.
* **Contras**: Consumo massivo de memória RAM (2GB+ mínimo); complexidade de configuração desproporcional para o escopo inicial.

---

## Decisão

Adotaremos uma **Estratégia Híbrida de Busca Inteligente**:

1. **Cardápio Digital & Autoatendimento (Customer-facing)**:
   * **Tecnologia**: **Meilisearch** rodando como container no microsserviço de cardápio (`menu-service`).
   * **Fluxo**: Quando um produto, categoria ou ingrediente é criado/alterado no `menu-service`, um evento assíncrono indexa o documento no Meilisearch com a chave do `tenant_id`.
   * **Funcionalidade**: Busca instantânea, correção de digitação, destaques (*highlighting*) e filtros por tags.

2. **Busca Operacional de Backoffice (Garçom, Caixa, Estoque e CRM)**:
   * **Tecnologia**: **PostgreSQL `pg_trgm` (Trigramas) + `tsvector` + `unaccent`**.
   * **Fluxo**: Consultas diretas no banco de dados relacional de cada microsserviço (`order-service`, `inventory-service`, `auth-service`).
   * **Funcionalidade**: Busca exata e parcial instantânea com garantias de consistência ACID.

---

## Mapeamento dos Casos de Uso de Busca Inteligente

| Caso de Uso | Domínio / Servidor | Motor Recomendado | Recursos Utilizados |
|---|---|---|---|
| Cardápio & Pratos (Autoatendimento) | `menu-service` | **Meilisearch** | Typo tolerance, Highlight, Filtro por Ingredientes/Dietas |
| Busca de Comandas / Mesas / Garçom | `dining-service` | **Postgres `pg_trgm`** | Busca parcial por número de mesa, nome do cliente ou código |
| Busca de Pedidos & Histórico (POS) | `order-service` | **Postgres `tsvector`** | Busca por código `#1234`, itens do pedido, faixa de preço |
| Busca de Insumos & Fornecedores | `inventory-service` | **Postgres `pg_trgm`** | Busca por nome do insumo, SKU, fornecedor |
| Busca de Clientes (CRM / Fidelidade) | `auth-service` | **Postgres `pg_trgm`** | Busca por telefone sanitizado, CPF, e-mail, nome |
