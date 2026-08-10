# 🔌 Guia de APIs e Protocolos de Comunicação — Restaurant Apps Platform

## 1. Convenções de RESTful APIs

A **Restaurant Apps Platform** expõe suas funcionalidades através de rotas RESTful no padrão HTTP/JSON, complementadas por WebSockets para funcionalidades de tempo real (KDS, Notificações do Garçom e Painel de Senhas).

### 1.1 Padronização de URLs
* Prefixos de versão mandatórios: `/api/v1/`
* Nomes de recursos no plural e em lowercase kebab-case: Exemplo: `/api/v1/menu/product-categories`
* Recursos aninhados para dependências claras: Exemplo: `/api/v1/dining/tables/{table_id}/commands`

### 1.2 Métodos HTTP e Semântica
* `GET`: Recuperação de recursos. Leitura idempotente.
* `POST`: Criação de recursos ou execução de comandos/ações (ex: `/orders/{id}/cancel`).
* `PUT`: Substituição completa de um recurso.
* `PATCH`: Atualização parcial de um recurso.
* `DELETE`: Remoção (ou Soft Delete) de um recurso.

---

## 2. Padrão de Resposta de Erro (RFC 7807 — Problem Details)

Todas as respostas de erro da API retornam estritamente a estrutura estandardizada `application/problem+json`:

```json
{
  "type": "https://api.restaurantapps.com.br/errors/insufficient-stock",
  "title": "Estoque Insuficiente",
  "status": 422,
  "detail": "O produto 'Hambúrguer Artesanal' possui apenas 2 unidades em estoque, mas foram solicitadas 5.",
  "instance": "/api/v1/orders",
  "code": "INSUFFICIENT_STOCK",
  "invalid_params": [
    {
      "name": "items[0].quantity",
      "reason": "Quantidade solicitada excede o limite disponível"
    }
  ],
  "timestamp": "2026-08-04T20:30:00Z"
}
```

---

## 3. Rate Limiting e Cabeçalhos HTTP

Todas as respostas de API contêm os seguintes cabeçalhos de controle de limite:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1722803400
```

Quando o limite é excedido, a API responde com status `429 Too Many Requests` e cabeçalho `Retry-After: 60`.

---

## 4. Protocolo de WebSockets em Tempo Real

Para o KDS (Kitchen Display System) e notificações instantâneas no app do garçom:
* Endpoint WebSocket: `wss://api.restaurantapps.com.br/ws/v1/kitchen/kds?tenant_id={tenant_id}&token={jwt}`
* Padrão de Mensagens JSON (Event Envelopes):

```json
{
  "event": "KDS_ITEM_STATUS_CHANGED",
  "tenant_id": "019124a1-7c2a-71b3-810a-3199d0c64921",
  "timestamp": "2026-08-04T20:30:15Z",
  "data": {
    "kds_item_id": "019124a5-99df-7f22-92bc-90a1f0a12b45",
    "order_id": "019124a5-1122-77bb-88cc-123456789abc",
    "table_number": 12,
    "product_name": "Picanha na Chapa 500g",
    "new_status": "PREPARING",
    "prep_time_minutes": 15
  }
}
```
