import type { APIRequestContext } from '@playwright/test';

/**
 * Portas fixas do stack de dev (`infra/scripts/dev-up.ps1`) — mesmo padrão
 * de `tests/integration/test_full_platform_flow.py`.
 */
export const AUTH_URL = 'http://localhost:8000';
export const RESTAURANT_URL = 'http://localhost:8001';
export const MENU_URL = 'http://localhost:8002';
export const DINING_URL = 'http://localhost:8003';
export const ORDER_URL = 'http://localhost:8005';
export const PAYMENT_URL = 'http://localhost:8007';

const OWNER_PASSWORD = 'senha-segura-123';

export interface SeededTenant {
  tenantId: string;
  slug: string;
  ownerEmail: string;
  ownerPassword: string;
  ownerToken: string;
  tableId: string;
  tableNumber: number;
  commandId: string;
  orderId: string;
  orderTotal: number;
}

/**
 * Cria um tenant novo e isolado (restaurante, dono, mesa, produto, comanda
 * aberta com um pedido real) via API — mesmo padrão de
 * `tests/integration/test_full_platform_flow.py`. Evita depender do seed de
 * demonstração mutável entre sessões (mesas já ficaram presas em estados
 * inconsistentes entre uma sessão e outra). Usado como "arrange" dos specs
 * E2E: a parte que de fato interessa testar é sempre via navegador real.
 */
export async function seedTenant(request: APIRequestContext): Promise<SeededTenant> {
  const unique = Math.random().toString(36).slice(2, 12);

  const restaurantResponse = await request.post(`${RESTAURANT_URL}/api/v1/restaurants`, {
    data: {
      slug: `e2e-${unique}`,
      trade_name: 'Restaurante E2E',
      legal_name: 'Restaurante E2E LTDA',
      cnpj: '12345678000199',
      phone: '11999999999',
      currency: 'BRL',
      service_fee_percent: 10.0,
    },
  });
  await assertOk(restaurantResponse, 'criar restaurante');
  const restaurant = await restaurantResponse.json();
  const tenantId: string = restaurant.id;
  const slug: string = restaurant.slug;

  const ownerEmail = `owner-${unique}@${unique}.com`;
  const registerResponse = await request.post(`${AUTH_URL}/api/v1/auth/register-owner`, {
    data: { tenant_id: tenantId, email: ownerEmail, password: OWNER_PASSWORD, name: 'Dono E2E' },
  });
  await assertOk(registerResponse, 'cadastrar dono');

  const loginResponse = await request.post(`${AUTH_URL}/api/v1/auth/login`, {
    data: { email: ownerEmail, password: OWNER_PASSWORD },
  });
  await assertOk(loginResponse, 'login do dono');
  const { access_token: ownerToken } = await loginResponse.json();
  const authHeaders = { Authorization: `Bearer ${ownerToken}` };

  const tableNumber = 1;
  const tableResponse = await request.post(`${DINING_URL}/api/v1/dining/tables`, {
    headers: authHeaders,
    data: { number: tableNumber, capacity: 4, qr_code_url: '' },
  });
  await assertOk(tableResponse, 'criar mesa');
  const table = await tableResponse.json();

  const categoryResponse = await request.post(`${MENU_URL}/api/v1/menu/categories`, {
    headers: authHeaders,
    data: { name: 'Lanches', display_order: 0 },
  });
  await assertOk(categoryResponse, 'criar categoria');
  const category = await categoryResponse.json();

  const productResponse = await request.post(`${MENU_URL}/api/v1/menu/products`, {
    headers: authHeaders,
    data: {
      category_id: category.id,
      name: 'X-Burger E2E',
      description: 'Hambúrguer de teste',
      price: 25.0,
      cost_price: 10.0,
      tax_rate: 0.0,
      photo_url: '',
      display_order: 0,
    },
  });
  await assertOk(productResponse, 'criar produto');
  const product = await productResponse.json();

  const commandResponse = await request.post(`${DINING_URL}/api/v1/dining/commands/open`, {
    headers: authHeaders,
    data: { table_number: tableNumber, customer_name: 'Cliente E2E' },
  });
  await assertOk(commandResponse, 'abrir comanda');
  const command = await commandResponse.json();

  const orderResponse = await request.post(`${ORDER_URL}/api/v1/orders`, {
    headers: { 'X-Tenant-Id': tenantId },
    data: {
      order_type: 'TABLE',
      table_number: tableNumber,
      command_id: command.id,
      items: [
        { product_id: product.id, product_name: product.name, unit_price: product.price, quantity: 2 },
      ],
    },
  });
  await assertOk(orderResponse, 'criar pedido');
  const order = await orderResponse.json();

  return {
    tenantId,
    slug,
    ownerEmail,
    ownerPassword: OWNER_PASSWORD,
    ownerToken,
    tableId: table.id,
    tableNumber,
    commandId: command.id,
    orderId: order.id,
    orderTotal: order.total_amount,
  };
}

/** Gera/rotaciona a secret de QR Code da mesa — usada pelo spec do
 * autoatendimento do cliente (`customer-web`), autenticado com o token do
 * dono (mesma rota que o botão "🔳" do `admin-web` chama). */
export async function rotateTableQrSecret(
  request: APIRequestContext,
  tableId: string,
  ownerToken: string,
): Promise<string> {
  const response = await request.post(
    `${DINING_URL}/api/v1/dining/tables/${tableId}/qr-secret/rotate`,
    { headers: { Authorization: `Bearer ${ownerToken}` } },
  );
  await assertOk(response, 'gerar secret do QR Code');
  const body = await response.json();
  return body.secret as string;
}

async function assertOk(
  response: { ok(): boolean; status(): number; text(): Promise<string> },
  action: string,
): Promise<void> {
  if (!response.ok()) {
    throw new Error(`Falha ao ${action}: HTTP ${response.status()} — ${await response.text()}`);
  }
}
