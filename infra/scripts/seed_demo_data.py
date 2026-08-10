"""Seeder mínimo de dados de demonstração — Restaurant Apps Platform.

Cria, contra o stack `docker-compose.dev.yml` já no ar (todos os 12
microsserviços respondendo em `localhost`), um tenant completo e coerente
para testar manualmente cada view de cada app (`admin-web`, `customer-web`,
`waiter-mobile`, `customer-mobile`):

  1. Um restaurante (tenant) — restaurant-service.
  2. Um usuário por papel RBAC (Owner, Manager, Caixa, Garçom, Cozinha) —
     auth-service. Garçom/Caixa/Cozinha recebem PIN de 4 dígitos para o
     login rápido usado pelos apps mobile.
  3. Mesas do salão — dining-service.
  4. Categorias + produtos do cardápio — menu-service.
  5. Insumos de estoque + fornecedor — inventory-service.
  6. Um cupom de marketing — marketing-service.
  7. Uma comanda aberta numa mesa + um pedido — dining-service/order-service
     (dispara a Saga `order.created`, populando o KDS automaticamente).
  8. Um caixa aberto — payment-service (pronto para receber o pagamento do
     pedido criado, deixado propositalmente PENDENTE para o testador seguir
     o fluxo manualmente pelo admin-web/waiter-mobile).

Idempotente por reexecução: usa um slug de restaurante fixo
(`RESTAURANT_SLUG`); se o restaurante já existir, ele é reaproveitado (não
recria usuários/mesas/produtos duplicados — apenas avisa e sai). Para
recomeçar do zero, troque o slug ou limpe o Postgres.

Uso:
    uv run python infra/scripts/seed_demo_data.py

Requer o stack de dev no ar (`infra/scripts/dev-up.ps1`/`.sh`).
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8000")
RESTAURANT_URL = os.environ.get("RESTAURANT_SERVICE_URL", "http://localhost:8001")
MENU_URL = os.environ.get("MENU_SERVICE_URL", "http://localhost:8002")
DINING_URL = os.environ.get("DINING_SERVICE_URL", "http://localhost:8003")
KITCHEN_URL = os.environ.get("KITCHEN_SERVICE_URL", "http://localhost:8004")
ORDER_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8005")
INVENTORY_URL = os.environ.get("INVENTORY_SERVICE_URL", "http://localhost:8006")
PAYMENT_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://localhost:8007")
MARKETING_URL = os.environ.get("MARKETING_SERVICE_URL", "http://localhost:8009")
NOTIFICATION_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:8010")

RESTAURANT_SLUG = "restaurante-demo"
DEMO_PASSWORD = "Demo@12345"

_TIMEOUT = httpx.Timeout(10.0)


def _fail(response: httpx.Response, step: str) -> None:
    print(f"\n✗ Falha em: {step}", file=sys.stderr)
    print(f"  HTTP {response.status_code} — {response.text}", file=sys.stderr)
    sys.exit(1)


def _post(
    client: httpx.Client, url: str, json: dict[str, Any], *, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    response = client.post(url, json=json, headers=headers)
    if response.status_code not in (200, 201):
        _fail(response, f"POST {url}")
    return response.json()


def main() -> None:  # noqa: PLR0915 - script de seed sequencial e linear, dividir pioraria a leitura
    # Windows abre stdout como cp1252 por padrão — força UTF-8 para os
    # marcadores ✓/✗ não quebrarem o script no meio da execução.
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    print("==============================================================")
    print("==> Seeder de dados de demonstração — Restaurant Apps Platform")
    print("==============================================================")

    with httpx.Client(timeout=_TIMEOUT) as client:
        try:
            client.get(f"{AUTH_URL}/api/v1/auth/health")
        except httpx.ConnectError:
            print(
                "✗ auth-service não respondeu em "
                f"{AUTH_URL}. Suba o stack primeiro: infra/scripts/dev-up.ps1",
                file=sys.stderr,
            )
            sys.exit(1)

        # --- 0) Reaproveita o restaurante se o slug já existir ------------
        existing = client.get(f"{RESTAURANT_URL}/api/v1/restaurants/by-slug/{RESTAURANT_SLUG}")
        if existing.status_code == httpx.codes.OK:
            print(
                f"\n⚠ Restaurante '{RESTAURANT_SLUG}' já existe (id={existing.json()['id']}).\n"
                "  O seeder é intencionalmente não-destrutivo — nada foi recriado.\n"
                "  Para recomeçar do zero, troque RESTAURANT_SLUG no script ou limpe o Postgres.\n"
                "  Veja infra/scripts/seed_demo_data.py para as credenciais já usadas na última "
                "execução, ou docs/TESTING_GUIDE.md."
            )
            return

        # --- 1) Restaurante (bootstrap do tenant) --------------------------
        restaurant = _post(
            client,
            f"{RESTAURANT_URL}/api/v1/restaurants",
            {
                "slug": RESTAURANT_SLUG,
                "trade_name": "Restaurante Demo",
                "legal_name": "Restaurante Demo Gastronomia LTDA",
                "cnpj": "12345678000199",
                "phone": "11999998888",
                "currency": "BRL",
                "service_fee_percent": 10.0,
            },
        )
        tenant_id = restaurant["id"]
        print(f"\n✓ Restaurante criado: {restaurant['trade_name']} (tenant_id={tenant_id})")

        # --- 2) Owner ---------------------------------------------------------
        owner_email = "dono@restaurantedemo.com.br"
        _post(
            client,
            f"{AUTH_URL}/api/v1/auth/register-owner",
            {
                "tenant_id": tenant_id,
                "email": owner_email,
                "password": DEMO_PASSWORD,
                "name": "Ana Dono",
            },
        )
        owner_login = _post(
            client,
            f"{AUTH_URL}/api/v1/auth/login",
            {"email": owner_email, "password": DEMO_PASSWORD},
        )
        owner_token = owner_login["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        print(f"✓ Owner criado: {owner_email} / senha {DEMO_PASSWORD}")

        # --- 2.1) Template de notificação "pedido pronto" ----------------------
        # Sem isso, o handler de `order.status_changed` do notification-service
        # não tem o que renderizar (ResourceNotFoundException) — a notificação
        # nunca chega a ser enfileirada.
        _post(
            client,
            f"{NOTIFICATION_URL}/api/v1/notifications/templates",
            {
                "code": "ORDER_READY",
                "channel": "IN_APP",
                "body": "Pedido da Mesa {table_number} está pronto!",
            },
            headers=owner_headers,
        )
        print("✓ Template de notificação criado: ORDER_READY (IN_APP)")

        # --- 3) Demais papéis (funcionários), criados pelo Owner --------------
        employees = [
            {
                "email": "gerente@restaurantedemo.com.br",
                "password": DEMO_PASSWORD,
                "name": "Marcos Gerente",
                "role": "MANAGER",
                "pin": "1111",
            },
            {
                "email": "caixa@restaurantedemo.com.br",
                "password": DEMO_PASSWORD,
                "name": "Carla Caixa",
                "role": "CASHIER",
                "pin": "2222",
            },
            {
                "email": "garcom@restaurantedemo.com.br",
                "password": DEMO_PASSWORD,
                "name": "Gustavo Garçom",
                "role": "WAITER",
                "pin": "3333",
            },
            {
                "email": "cozinha@restaurantedemo.com.br",
                "password": DEMO_PASSWORD,
                "name": "Karina Cozinha",
                "role": "KITCHEN_STAFF",
                "pin": "4444",
            },
        ]
        for employee in employees:
            _post(client, f"{AUTH_URL}/api/v1/auth/employees", employee, headers=owner_headers)
            print(
                f"✓ Funcionário criado: {employee['email']} / senha {DEMO_PASSWORD} "
                f"/ PIN {employee['pin']} ({employee['role']})"
            )

        # --- 4) Mesas do salão --------------------------------------------
        tables = []
        for number, capacity in [(1, 2), (2, 4), (3, 4), (4, 6), (5, 2)]:
            table = _post(
                client,
                f"{DINING_URL}/api/v1/dining/tables",
                {"number": number, "capacity": capacity, "qr_code_url": ""},
                headers=owner_headers,
            )
            tables.append(table)
        print(f"✓ {len(tables)} mesas cadastradas (1 a 5)")

        # --- 5) Cardápio: categorias + produtos ----------------------------
        category_specs = [
            (
                "Lanches",
                [
                    ("X-Burger Demo", "Pão, hambúrguer 180g, queijo e salada.", 28.90, 12.0),
                    ("X-Bacon Demo", "Pão, hambúrguer 180g, bacon e queijo.", 32.90, 14.0),
                ],
            ),
            (
                "Bebidas",
                [
                    ("Refrigerante Lata", "350ml, gelado.", 7.50, 2.5),
                    ("Suco Natural", "Copo 300ml.", 9.90, 3.0),
                ],
            ),
            (
                "Sobremesas",
                [
                    ("Petit Gateau", "Com sorvete de creme.", 21.90, 8.0),
                ],
            ),
        ]
        products: list[dict[str, Any]] = []
        for order_index, (category_name, product_specs) in enumerate(category_specs):
            category = _post(
                client,
                f"{MENU_URL}/api/v1/menu/categories",
                {"name": category_name, "display_order": order_index},
                headers=owner_headers,
            )
            for p_order, (name, description, price, cost) in enumerate(product_specs):
                product = _post(
                    client,
                    f"{MENU_URL}/api/v1/menu/products",
                    {
                        "category_id": category["id"],
                        "name": name,
                        "description": description,
                        "price": price,
                        "cost_price": cost,
                        "tax_rate": 0.0,
                        "photo_url": "",
                        "display_order": p_order,
                    },
                    headers=owner_headers,
                )
                products.append(product)
        print(f"✓ {len(category_specs)} categorias e {len(products)} produtos cadastrados")

        # --- 6) Estoque: fornecedor + insumos -------------------------------
        # (rota de fornecedor é só leitura no router atual — insumo aceita
        # supplier_id opcional, então seguimos sem fornecedor dedicado)
        inventory_items = [
            ("Pão de Hambúrguer", "UN", 200.0, 30.0),
            ("Carne Bovina 180g", "UN", 150.0, 20.0),
            ("Refrigerante Lata 350ml", "UN", 100.0, 15.0),
        ]
        for name, unit, initial_qty, min_qty in inventory_items:
            _post(
                client,
                f"{INVENTORY_URL}/api/v1/inventory/items",
                {
                    "name": name,
                    "unit": unit,
                    "initial_quantity": initial_qty,
                    "minimum_quantity": min_qty,
                },
                headers=owner_headers,
            )
        print(f"✓ {len(inventory_items)} insumos de estoque cadastrados")

        # --- 7) Cupom de marketing -----------------------------------------
        now = datetime.now(UTC)
        _post(
            client,
            f"{MARKETING_URL}/api/v1/marketing/coupons",
            {
                "code": "DEMO10",
                "discount_type": "PERCENTAGE",
                "discount_value": 10.0,
                "valid_from": now.isoformat(),
                "valid_until": (now + timedelta(days=90)).isoformat(),
                "max_uses": 100,
            },
            headers=owner_headers,
        )
        print("✓ Cupom de marketing criado: DEMO10 (10% off)")

        # --- 8) Comanda aberta na mesa 1 + pedido (dispara a Saga) ----------
        command = _post(
            client,
            f"{DINING_URL}/api/v1/dining/commands/open",
            {"table_number": 1, "customer_name": "Cliente Demo", "customer_cpf": None},
            headers=owner_headers,
        )
        print(f"✓ Comanda aberta na Mesa 1 (command_id={command['id']})")

        burger = products[0]
        soda = products[2]
        order = _post(
            client,
            f"{ORDER_URL}/api/v1/orders",
            {
                "order_type": "TABLE",
                "table_number": 1,
                "items": [
                    {
                        "product_id": burger["id"],
                        "product_name": burger["name"],
                        "unit_price": burger["price"],
                        "quantity": 2,
                    },
                    {
                        "product_id": soda["id"],
                        "product_name": soda["name"],
                        "unit_price": soda["price"],
                        "quantity": 2,
                    },
                ],
            },
            headers={"X-Tenant-Id": tenant_id, **owner_headers},
        )
        print(
            f"✓ Pedido criado na Mesa 1 (order_id={order['id']}, total=R$ {order['total_amount']:.2f})"
            " — a Saga deve populá-lo no KDS em alguns segundos."
        )

        # --- 9) Caixa aberto (pronto para receber o pagamento do pedido) ---
        # operator_id = próprio dono logado (TokenResponse.user.id)
        cash_register = _post(
            client,
            f"{PAYMENT_URL}/api/v1/payments/cash-registers",
            {"operator_id": owner_login["user"]["id"], "opening_amount": 200.0},
            headers=owner_headers,
        )
        print(
            f"✓ Caixa aberto com R$ 200,00 (cash_register_id={cash_register['id']})"
            " — pedido deixado PENDENTE de pagamento de propósito, para testar o fluxo manualmente."
        )

    print("\n==============================================================")
    print("==> Seed concluído com sucesso.")
    print("==============================================================")
    print(f"Restaurante: Restaurante Demo (slug={RESTAURANT_SLUG}, tenant_id={tenant_id})")
    print(f"\nCustomer-web (cardápio público): http://localhost:3000/?r={RESTAURANT_SLUG}&table=1")
    print("\nCredenciais (senha e-mail/senha e PIN 4 dígitos para apps mobile):")
    print(f"  Owner            : {owner_email} / {DEMO_PASSWORD}")
    for employee in employees:
        print(
            f"  {employee['role']:<14}: {employee['email']} / {DEMO_PASSWORD} / PIN {employee['pin']}"
        )
    print(f"\ntenant_id (para login por PIN nos apps mobile): {tenant_id}")


if __name__ == "__main__":
    main()
