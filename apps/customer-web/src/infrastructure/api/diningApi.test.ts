import { afterEach, describe, expect, it, vi } from 'vitest';
import { customerCloseCommand, getOpenCommandForTable } from './diningApi';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('getOpenCommandForTable', () => {
  it('sends the table secret as a query param and the tenant header', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: 'command-1', status: 'OPEN', service_fee_charged: true }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await getOpenCommandForTable('tenant-1', 5, 'secret-1');

    expect(result.id).toBe('command-1');
    const [url, requestInit] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/v1/dining/tables/5/open-command?secret=secret-1');
    expect(requestInit.headers['X-Tenant-Id']).toBe('tenant-1');
  });

  it('throws an ApiError when the secret is invalid or expired', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ title: 'InvalidOrExpiredQrSecretError', detail: 'QR Code inválido ou expirado.' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(getOpenCommandForTable('tenant-1', 5, 'errada')).rejects.toMatchObject({ status: 401 });
  });
});

describe('customerCloseCommand', () => {
  it('posts to the customer-close endpoint with the secret as a query param', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: 'command-1', status: 'CLOSED' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await customerCloseCommand('tenant-1', 'command-1', 'secret-1');

    expect(result.status).toBe('CLOSED');
    const [url, requestInit] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/v1/dining/commands/command-1/customer-close?secret=secret-1');
    expect(requestInit.method).toBe('POST');
  });
});
