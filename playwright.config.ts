import { defineConfig } from '@playwright/test';

/**
 * Config do Playwright — raiz do monorepo (docs/testing/test_strategy.md
 * já reservava `tests/e2e/` pra isso). Não sobe Docker nem os frontends
 * sozinho: pressupõe o stack + `admin-web`(:3001)/`customer-web`(:3000) já
 * rodando (`infra/scripts/dev-up.ps1` + `apps-up.ps1`), mesmo pressuposto
 * já documentado pros testes de integração `httpx` (`tests/integration/`).
 * Cada spec cria seu próprio tenant isolado via API antes de abrir o
 * navegador (`tests/e2e/support/seedTenant.ts`) — não depende do seed de
 * demonstração, que já vimos ficar em estados inconsistentes entre sessões.
 */
export default defineConfig({
  testDir: 'tests/e2e',
  // Só 2 specs hoje, ambos batendo nos mesmos dev servers Vite
  // (admin-web/customer-web) — rodar em paralelo faz os dois competirem
  // pela primeira compilação sob demanda de cada rota (Vite dev só
  // transforma um módulo na primeira vez que é visitado), o que já foi
  // observado estourando os 60s de timeout numa primeira rodada "fria".
  // Serial evita essa contenção sem custo real (a suíte já é rápida).
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: 'list',
  // Checkout de verdade atravessa 5 microsserviços (dining/order/payment/
  // restaurant + o navegador) — folga maior que o default de 30s, e mais
  // ainda que os 60s originais: a primeira visita de uma rota sob o Vite
  // dev (compilação sob demanda) já se mostrou levar mais que isso.
  timeout: 90_000,
  use: {
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
});
