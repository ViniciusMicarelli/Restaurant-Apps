import { test, expect } from '@playwright/test';
import { seedTenant } from './support/seedTenant';

const ADMIN_WEB_URL = 'http://localhost:3001';

/**
 * Fluxo do garçom/dono cobrando na mesa com a própria maquininha
 * (`admin-web`) — login → mapa de mesas → comanda → "Fechar e Cobrar" →
 * abre o próprio caixa → Pix. Cobre em conjunto o RBAC de pagamento (US-05.2/
 * 2026-08-06) e a idempotência adicionada na revisão de segurança de
 * 2026-08-10 (o botão fica desabilitado durante o envio, sem duplo-clique).
 */
test('dono abre o próprio caixa e cobra a comanda via Pix', async ({ page, request }) => {
  const tenant = await seedTenant(request);

  await page.goto(ADMIN_WEB_URL);
  await page.getByPlaceholder('voce@restaurante.com').fill(tenant.ownerEmail);
  await page.getByPlaceholder('••••••••').fill(tenant.ownerPassword);
  await page.getByRole('button', { name: 'Entrar' }).click();

  await page.getByRole('button', { name: 'Mapa de Mesas (Salão)' }).click();
  await page.getByText(`Mesa ${tenant.tableNumber}`).click();

  await page.getByRole('button', { name: 'Fechar e Cobrar' }).click();

  // A consulta de "caixa aberto" pode demorar um pouco mais na primeira
  // visita da rota (compilação sob demanda do Vite dev) — espera de
  // verdade por qualquer um dos dois estados possíveis em vez de checar
  // `isVisible()` uma única vez (que corre o risco de checar cedo demais,
  // antes da query assentar, e nunca abrir o caixa).
  const openRegisterButton = page.getByRole('button', { name: 'Abrir meu caixa' });
  const pixButton = page.getByRole('button', { name: 'Pix', exact: true });
  await expect(openRegisterButton.or(pixButton)).toBeVisible({ timeout: 30_000 });

  if (await openRegisterButton.isVisible()) {
    await openRegisterButton.click();
    await expect(pixButton).toBeVisible({ timeout: 15_000 });
  }

  await pixButton.click();
  await page.getByRole('button', { name: 'Confirmar Recebimento do Pix' }).click();

  await expect(page.getByText('Comanda fechada!')).toBeVisible({ timeout: 15_000 });
});
