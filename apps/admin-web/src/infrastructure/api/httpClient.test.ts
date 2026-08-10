import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiRequest, ApiError } from './httpClient';
import { useSessionStore } from '../state/sessionStore';

const BASE_URL = 'http://localhost:9999';

afterEach(() => {
  vi.unstubAllGlobals();
  useSessionStore.getState().logout();
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
    expect(fetchMock).toHaveBeenCalledWith(
      `${BASE_URL}/ping`,
      expect.objectContaining({ method: 'GET' }),
    );
  });

  it('attaches the Bearer token from the session store', async () => {
    useSessionStore.getState().login({
      accessToken: 'test-token-123',
      refreshToken: 'refresh-123',
      user: { id: '1', tenantId: 't1', email: 'a@b.com', name: 'Ana', role: 'MANAGER' },
    });
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await apiRequest(BASE_URL, '/secure');

    const [, requestInit] = fetchMock.mock.calls[0];
    expect(requestInit.headers.Authorization).toBe('Bearer test-token-123');
  });

  it('never attaches Authorization when skipAuth is true', async () => {
    useSessionStore.getState().login({
      accessToken: 'test-token-123',
      refreshToken: 'refresh-123',
      user: { id: '1', tenantId: 't1', email: 'a@b.com', name: 'Ana', role: 'MANAGER' },
    });
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await apiRequest(BASE_URL, '/public', { skipAuth: true });

    const [, requestInit] = fetchMock.mock.calls[0];
    expect(requestInit.headers.Authorization).toBeUndefined();
  });

  it('throws an ApiError with the RFC 7807 detail on failure', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ title: 'InvalidCouponException', detail: 'Cupom expirado.', code: 'INVALID_COUPON' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(apiRequest(BASE_URL, '/coupons/apply')).rejects.toMatchObject({
      message: 'Cupom expirado.',
      status: 409,
      code: 'INVALID_COUPON',
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
