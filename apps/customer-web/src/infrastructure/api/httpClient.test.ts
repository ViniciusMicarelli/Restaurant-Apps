import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiRequest, ApiError } from './httpClient';

const BASE_URL = 'http://localhost:9999';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('apiRequest', () => {
  it('returns the parsed JSON body on success', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ hello: 'world' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await apiRequest<{ hello: string }>(BASE_URL, '/ping');

    expect(result).toEqual({ hello: 'world' });
  });

  it('sends the X-Tenant-Id header when tenantId is provided', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await apiRequest(BASE_URL, '/menu/products', { tenantId: 'tenant-123' });

    const [, requestInit] = fetchMock.mock.calls[0];
    expect(requestInit.headers['X-Tenant-Id']).toBe('tenant-123');
  });

  it('throws an ApiError with the RFC 7807 detail on failure', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ title: 'ResourceNotFoundException', detail: 'Restaurante não encontrado.' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(apiRequest(BASE_URL, '/restaurants/by-slug/nope')).rejects.toMatchObject({
      message: 'Restaurante não encontrado.',
      status: 404,
    });
  });

  it('falls back to a generic message when the error body is not JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      json: async () => {
        throw new Error('not json');
      },
    });
    vi.stubGlobal('fetch', fetchMock);

    const error = await apiRequest(BASE_URL, '/down').catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(502);
  });
});
