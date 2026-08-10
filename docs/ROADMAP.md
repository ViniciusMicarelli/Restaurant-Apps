# 🗺️ Roadmap de Desenvolvimento — Restaurant Apps Platform

## Visão Geral do Roadmap

O desenvolvimento da **Restaurant Apps Platform** está estruturado em 5 fases progressivas, priorizando a estabilidade do core operacional (Cardápio, Salão, Mesas, Comandas, Pedidos e Cozinha) antes da expansão para inteligência de negócios, delivery avançado e multi-tenancy SaaS em escala.

---

## 📅 Fase 1: Fundação & MVP Operacional (Core Salão, Comandas e Cozinha)

> **Objetivo**: Permitir que um restaurante operante faça atendimento presencial completo (Mesa/Comanda), envie pedidos para a cozinha (KDS) e realize o fechamento do caixa.

* **Backend & Infra base**:
  * Monorepo scaffolded com FastAPI, SQLAlchemy 2.0 Async, Alembic e PostgreSQL.
  * Módulo `auth` (Autenticação JWT/OAuth2, RBAC inicial com Roles: Dono, Gerente, Garçom, Cozinheiro).
  * Módulo `restaurant` (Configurações iniciais do estabelecimento).
* **Cardápio & Estoque básico**:
  * Módulo `menu` (Categorias, Produtos, Opções, Adicionais).
  * Módulo `inventory` (Cadastro de insumos e baixa automática simples).
* **Operação de Salão & Cozinha**:
  * Módulo `dining` (Gestão de Mesas e Abertura/Fechamento de Comandas).
  * Módulo `orders` (Motor de criação de pedidos presenciais).
  * Módulo `kitchen` (KDS em tempo real via WebSocket com status: PENDENTE, PREPARANDO, PRONTO).
* **Caixa & Pagamentos**:
  * Módulo `payments` (Abertura/Fechamento de Caixa, recebimento em Dinheiro, Cartão e Pix estático).
* **Interfaces**:
  * `admin-web`: Painel do Gestor (Cadastro de produtos, mesas e relatórios de vendas do dia).
  * `waiter-mobile` (Flutter): App do garçom para abertura de mesa e lançamento de pedidos.

---

## 📅 Fase 2: Autoatendimento, Filas Virtuais e Fidelidade

> **Objetivo**: Empoderar o cliente final no salão e na espera, reduzindo filas e custo operacional.

* **Cardápio Digital QR Code & Pedido na Mesa**:
  * `customer-web` (React/Vite PWA): Cardápio interativo via QR Code da mesa. O próprio cliente faz o pedido, que cai direto no KDS.
* **Fila de Espera Virtual & Reservas**:
  * Módulo `dining` (Fila virtual com entrada via QR Code na entrada do restaurante e notificações via WhatsApp).
  * Gestão de reservas com mapa visual do salão.
* **Programa de Fidelidade & Cupons**:
  * Módulo `marketing` (Criação de cupons de desconto e acúmulo de pontos por valor gasto).
* **Pagamento pelo cliente no `customer-web`** (US-05.4, entregue em 2026-08-10): o cliente fecha e paga a própria comanda pelo celular a qualquer momento (botão "Fechar minha conta"), sem precisar esperar a maquininha — canal complementar ao pagamento presencial do garçom, não substituto.

---

## 3. Fase 3: Delivery Integrado, Retirada e Webhooks

> **Objetivo**: Expandir as vendas para o ambiente online fora do restaurante.

* Módulo `delivery`:
  * Integração com iFood, Rappi e 99Food via APIs/Webhooks.
  * Gestão de entregadores próprios ou terceirizados (Logística de despacho).
  * Módulo de Retirada (Takeout/Drive-thru) com indicação de tempo estimado.
* `customer-mobile` (Flutter): App próprio de Delivery e Fidelidade com marca própria ou marketplace da rede.

---

## 4. Fase 4: Inteligência Financeira, DRE, Auditoria & Previsão de Estoque

> **Objetivo**: Fornecer inteligência estratégica para o gestor aumentar a margem de lucro.

* Módulo `analytics`:
  * Relatório de DRE Operacional (Demonstrativo de Resultado do Exercício).
  * ABC do Cardápio (Produtos mais lucrativos x mais vendidos).
  * Auditoria avançada de sangrias, cancelamentos de itens e descontos aplicados.
* Módulo `inventory` avançado:
  * Alertas preditivos de ruptura de estoque com base no histórico de vendas.
  * Sugestão de pedidos de compra para fornecedores.

---

## 5. Fase 5: SaaS Multi-Tenant Enterprise & Expansão

> **Objetivo**: Escalar a plataforma para franquias, redes de restaurantes e modelo SaaS global.

* Multi-Tenancy avançado: particionamento por `tenant_id` e réplicas de leitura dedicadas para tenants de grande volume, mantendo a estratégia de Row-Level Isolation da `ADR-003` (schema-per-tenant foi avaliado e rejeitado nessa ADR; não é mais uma direção considerada).
* Painel de Gestão Multi-loja (Visão consolidada da rede).
* Split de pagamentos automatizado em gateways de pagamento.
* API Pública e Marketplace de Integrações para parceiros.
