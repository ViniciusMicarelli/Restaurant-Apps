import { afterEach, describe, expect, it, vi } from 'vitest';
import { submitCustomerPayment } from './paymentApi';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('submitCustomerPayment', () => {
  it('posts to the customer-checkout endpoint with the tenant header', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ id: 'payment-1', order_id: 'order-1', cash_register_id: null, total_amount: 50, status: 'APPROVED' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await submitCustomerPayment(
      'tenant-1',
      {
        table_number: 5,
        secret: 'secret-1',
        splits: [{ payment_method: 'PIX', amount: 50 }],
      },
      'idem-key-1',
    );

    expect(result.status).toBe('APPROVED');
    expect(result.cash_register_id).toBeNull();

    const [url, requestInit] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/v1/payments/customer-checkout');
    expect(requestInit.method).toBe('POST');
    expect(requestInit.headers['X-Tenant-Id']).toBe('tenant-1');
    expect(requestInit.headers['Idempotency-Key']).toBe('idem-key-1');
    expect(JSON.parse(requestInit.body)).toMatchObject({ table_number: 5, secret: 'secret-1' });
  });

  it('throws an ApiError when the table secret is invalid', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ title: 'InvalidTableSecretException', detail: 'QR Code inválido ou expirado.' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      submitCustomerPayment(
        'tenant-1',
        {
          table_number: 5,
          secret: 'errada',
          splits: [{ payment_method: 'PIX', amount: 50 }],
        },
        'idem-key-2',
      ),
    ).rejects.toMatchObject({ status: 401 });
  });

  it('never sends order_id/command_id/expected_total in the body (revisão de segurança, 2026-08-10)', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ id: 'payment-1', order_id: 'order-1', cash_register_id: null, total_amount: 50, status: 'APPROVED' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await submitCustomerPayment(
      'tenant-1',
      {
        table_number: 5,
        secret: 'secret-1',
        splits: [{ payment_method: 'PIX', amount: 50 }],
      },
      'idem-key-3',
    );

    const [, requestInit] = fetchMock.mock.calls[0];
    const sentBody = JSON.parse(requestInit.body);
    expect(sentBody).not.toHaveProperty('order_id');
    expect(sentBody).not.toHaveProperty('command_id');
    expect(sentBody).not.toHaveProperty('expected_total');
  });
});
