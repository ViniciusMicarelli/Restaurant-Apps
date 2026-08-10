# 📋 Backlog de Funcionalidades — Restaurant Apps Platform

## 1. Épico: Autenticação, Usuários & Multi-Tenancy (EP-01)
* [ ] **US-01.1**: Como desenvolvedor, quero configurar a infraestrutura de banco de dados e suporte a `tenant_id` em todas as tabelas com SQLAlchemy 2.0.
* [ ] **US-01.2**: Como gestor, quero cadastrar meu restaurante e configurar informações básicas (Razão social, CNPJ, moeda, taxa de serviço).
* [ ] **US-01.3**: Como usuário, quero realizar login via JWT com e-mail/senha e obter um token seguro HTTP-Only.
* [ ] **US-01.4**: Como gerente, quero criar perfis de funcionários (Garçom, Cozinheiro, Caixa) e atribuir PINs de 4 dígitos para acesso rápido no POS/Mobile.

---

## 2. Épico: Gestão de Cardápio & Insumos (EP-02)
* [ ] **US-02.1**: Como gestor, quero criar categorias de produtos (ex: Bebidas, Lanches, Sobremesas) com ordenação personalizada.
* [ ] **US-02.2**: Como gestor, quero cadastrar produtos com foto, preço de venda, custo, alíquota fiscal e adicionais.
* [ ] **US-02.3**: Como gestor, quero criar grupos de adicionais (ex: Ponto da Carne, Ingredientes Extra) com limites mínimo e máximo de escolha.
* [ ] **US-02.4**: Como gestor, quero cadastrar a ficha técnica do produto associando insumos do estoque para baixa automática.

---

## 3. Épico: Salão, Mesas e Comandas (EP-03)
* [ ] **US-03.1**: Como gerente, quero cadastrar o mapa de mesas do salão (número, capacidade e QR Code estático gerado).
* [ ] **US-03.2**: Como garçom, quero visualizar o status de todas as mesas em tempo real (Livre, Ocupada, Reservada, Aguardando Limpeza) no app mobile.
* [ ] **US-03.3**: Como garçom, quero abrir uma comanda/sessão de mesa associando o nome ou CPF do cliente.
* [ ] **US-03.4**: Como garçom, quero transferir itens entre comandas ou trocar clientes de mesa com registro em auditoria.
* [x] **US-03.5**: Como garçom, quero marcar uma mesa "Aguardando Limpeza" como limpa/liberada — resolvido em 2026-08-07 (`POST /tables/{id}/mark-cleaned`, botão "Mesa Limpa" no `admin-web`, toque na mesa no `waiter-mobile`).

---

## 4. Épico: Motor de Pedidos & KDS da Cozinha (EP-04)
* [ ] **US-04.1**: Como garçom, quero selecionar produtos com seus adicionais e observações e enviar o pedido para a cozinha.
* [ ] **US-04.2**: Como cozinheiro, quero visualizar os pedidos em um painel KDS (Kitchen Display System) categorizados por tempo de espera e status.
* [ ] **US-04.3**: Como cozinheiro, quero alterar o status do item/pedido para "EM PREPARO" e "PRONTO" com notificação instantânea para o garçom via WebSocket.
* [ ] **US-04.4**: Como gerente, quero cancelar um pedido enviado com motivo obrigatório e registro imutável em log de auditoria.

---

## 5. Épico: Caixa & Pagamentos (EP-05)
* [ ] **US-05.1**: Como operador de caixa, quero realizar a abertura do caixa informando o valor de troco inicial (suprimento).
* [ ] **US-05.2**: Como operador de caixa, quero buscar a comanda da mesa, aplicar descontos autorizados e selecionar as formas de pagamento (Dinheiro, Cartão, Pix).
* [ ] **US-05.3**: Como operador de caixa, quero efetuar o fechamento cego do caixa com relatório de divergência e histórico de sangrias.
* [x] **US-05.4**: Como cliente, quero poder pagar minha própria comanda pelo `customer-web`, sem precisar esperar a maquininha — resolvido em 2026-08-10 (botão "Fechar minha conta" sempre disponível no painel "Meu Pedido" assim que há pedidos lançados — sem depender de o garçom liberar nada; Cartão/Pix simulados, sem assinatura; `GET /tables/{n}/open-command` + `POST /commands/{id}/customer-close` no `dining-service`, `POST /payments/customer-checkout` no `payment-service`, autorizados pela secret de QR Code da mesa em vez de papel de equipe. Continua complementar ao fluxo do garçom com a maquininha, não o substitui — "quem chegar primeiro" fecha a comanda).
