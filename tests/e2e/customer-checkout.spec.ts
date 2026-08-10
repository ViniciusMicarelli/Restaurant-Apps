import { test, expect } from '@playwright/test';
import { PAYMENT_URL, rotateTableQrSecret, seedTenant } from './support/seedTenant';

const CUSTOMER_WEB_URL = 'http://localhost:3000';

/**
 * Autoatendimento do cliente (`customer-web`, US-05.4) — protege
 * exatamente o fluxo do bug crítico corrigido na revisão de segurança de
 * 2026-08-10: um cliente com a própria secret de mesa válida paga a
 * comanda inteira sem conseguir controlar `order_id`/`command_id`/
 * `expected_total` (removidos do contrato). Confirma via API, ao final,
 * que o valor realmente cobrado é o total real computado pelo servidor.
 */
test('cliente fecha e paga a própria conta via Pix', async ({ page, request }) => {
  const tenant = await seedTenant(request);
  const secret = await rotateTableQrSecret(request, tenant.tableId, tenant.ownerToken);

  await page.goto(
    `${CUSTOMER_WEB_URL}/?r=${tenant.slug}&table=${tenant.tableNumber}&secret=${secret}`,
  );

  // Cardápio carregado com a secret válida (gate obrigatório desde 2026-08-06).
  await expect(page.getByText('QR Code inválido ou expirado')).not.toBeVisible();

  await page.getByRole('button', { name: 'Meu Pedido' }).click();
  await expect(page.getByText('X-Burger E2E')).toBeVisible({ timeout: 15_000 });

  await page.getByRole('button', { name: 'Fechar minha conta' }).click();
  await page.getByRole('button', { name: 'Pix', exact: true }).click();
  await page.getByRole('button', { name: 'Já paguei pelo Pix' }).click();

  await expect(page.getByText('Obrigado! Sua conta foi paga.')).toBeVisible({ timeout: 15_000 });
  // A celebração fecha sozinha (~2.2s) e o painel troca pra tela de
  // agradecimento — confirma que o fluxo terminou de verdade, não só que
  // o modal de pagamento fechou.
  await expect(page.getByText('Obrigado pela visita!')).toBeVisible({ timeout: 10_000 });

  // Confere no servidor (não só na tela) que o valor cobrado foi o total
  // real da comanda, não um valor que o cliente poderia ter forjado.
  const paymentsResponse = await request.get(
    `${PAYMENT_URL}/api/v1/payments?command_id=${tenant.commandId}`,
    { headers: { Authorization: `Bearer ${tenant.ownerToken}` } },
  );
  expect(paymentsResponse.ok()).toBeTruthy();
  const payments = await paymentsResponse.json();
  expect(payments).toHaveLength(1);
  expect(payments[0].total_amount).toBe(tenant.orderTotal);
  expect(payments[0].cash_register_id).toBeNull();
  expect(payments[0].command_id).toBe(tenant.commandId);
});
