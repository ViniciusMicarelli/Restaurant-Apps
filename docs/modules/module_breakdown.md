# 🧩 Detalhamento dos Módulos do Sistema — Restaurant Apps Platform

## Visão Geral dos Módulos

A plataforma é dividida em 12 módulos de negócio isolados (*Bounded Contexts*), cada um responsável por um domínio específico da operação de um restaurante.

---

## 1. Módulo Auth & Security (`modules/auth`)
* **Responsabilidades**: Autenticação de usuários, emissão e revogação de tokens JWT, controle de sessão, hash de senhas, validação de PIN de garçom/caixa, autorização RBAC (Roles) e ABAC (Atributos/Condições).
* **Entidades**: `User`, `Employee`, `Role`, `Permission`, `UserSession`.

## 2. Módulo Restaurant (`modules/restaurant`)
* **Responsabilidades**: Gestão dos dados cadastrais do restaurante, configurações operacionais (taxa de serviço, horário de funcionamento, regras de cancelamento, moedas e fiscais), gestão de planos e assinaturas SaaS.
* **Entidades**: `Restaurant`, `RestaurantSetting`, `SubscriptionPlan`.

## 3. Módulo Menu & Cardápio (`modules/menu`)
* **Responsabilidades**: Estruturação completa do cardápio. Categorias, produtos, grupos de opções (adicionais/opcionais), fotos, variações de preço, combos e disponibilidade por horário/dia da semana.
* **Entidades**: `Category`, `Product`, `ProductOptionGroup`, `ProductOption`, `Combo`, `ComboItem`.

## 4. Módulo Salão & Atendimento (`modules/dining`)
* **Responsabilidades**: Gestão do mapa de mesas, comandas presenciais, fila de espera virtual (com notificação de posição via WhatsApp) e agendamento de reservas de mesas.
* **Entidades**: `Table`, `Command` (Comanda), `VirtualQueue`, `Reservation`.

## 5. Módulo Pedidos (`modules/orders`)
* **Responsabilidades**: Motor central de pedidos. Recebimento de pedidos de múltiplas origens (Mesa, Balcão, QR Code, Delivery, Retirada), cálculo de totais, adicionais, descontos, transição de estados do pedido (PENDENTE, EM PREPARO, PRONTO, ENTREGUE, CANCELADO).
* **Entidades**: `Order`, `OrderItem`, `OrderItemOption`, `OrderHistory`.

## 6. Módulo Cozinha / KDS (`modules/kitchen`)
* **Responsabilidades**: Kitchen Display System (KDS). Exibição em tempo real de itens por estação de trabalho (Cozinha Quente, Bar, Sobremesas), controle de tempo de preparo, alertas de atraso e integração com impressoras térmicas ESC/POS.
* **Entidades**: `KDSStation`, `KDSItem`, `KDSLog`.

## 7. Módulo Estoque & Ficha Técnica (`modules/inventory`)
* **Responsabilidades**: Controle de insumos, ficha técnica de produtos (baixa automática na venda), movimentação manual (entradas, perdas, devoluções), contagem de estoque (inventário) e alertas de estoque mínimo.
* **Entidades**: `InventoryItem`, `Recipe`, `RecipeItem`, `StockMovement`, `Supplier`.

## 8. Módulo Pagamentos & Caixa (`modules/payments`)
* **Responsabilidades**: Abertura, suprimento, sangria e fechamento cego de caixas operacionais. Integração com gateways para pagamento em Cartão de Crédito/Débito, Pix dinâmico com QR Code, troco e emissão fiscal.
* **Entidades**: `CashRegister`, `CashMovement`, `Payment`, `PaymentSplit`.

## 9. Módulo Delivery & Retirada (`modules/delivery`)
* **Responsabilidades**: Integração com plataformas terceiras (iFood, Rappi), gestão de entregadores próprios, cálculo de taxa de entrega por raio/geolocalização e acompanhamento de status de entrega.
* **Entidades**: `DeliveryOrder`, `DeliveryDriver`, `DeliveryZone`.

## 10. Módulo Marketing & Fidelidade (`modules/marketing`)
* **Responsabilidades**: Criação de cupons de desconto (por valor fixo, percentual ou frete grátis), programas de pontos/fidelidade do restaurante e réguas de relacionamento com o cliente.
* **Entidades**: `Coupon`, `LoyaltyAccount`, `LoyaltyTransaction`.

## 11. Módulo Notificações (`modules/notification`)
* **Responsabilidades**: Disparo de mensagens assíncronas via Push Notification (Web/Mobile), mensagens automáticas via WhatsApp (Notificação de fila, confirmação de reserva) e e-mails transacionais.
* **Entidades**: `Notification`, `NotificationTemplate`, `NotificationLog`.

## 12. Módulo Analytics & Auditoria (`modules/analytics`)
* **Responsabilidades**: Geração de relatórios gerenciais, vendas por hora/dia/garçom, curva ABC de produtos, DRE simplificado e registros imutáveis de auditoria técnica e operacional.
* **Entidades**: `AuditLog`, `DailySalesReport`, `WaitstaffPerformance`.
