import { apiRequest } from './httpClient';

const PAYMENT_SERVICE_URL = import.meta.env.VITE_PAYMENT_SERVICE_URL;

export type CustomerPaymentMethod = 'CREDIT_CARD' | 'DEBIT_CARD' | 'PIX';

export interface CustomerCheckoutPayload {
  table_number: number;
  secret: string;
  // `order_id`/`command_id`/`expected_total` NUNCA vão no payload (revisão
  // de segurança, 2026-08-10) — o servidor descobre a comanda aberta e o
  // valor real dos pedidos sozinho (dining-service/order-service/
  // restaurant-service), pra um cliente mal-intencionado não conseguir
  // forjar o valor cobrado nem vincular o pagamento à comanda de outra
  // mesa. O `amount` de cada parcela abaixo ainda é validado contra esse
  // total real antes de aprovar.
  splits: { payment_method: CustomerPaymentMethod; amount: number }[];
  card_last4?: string;
  card_holder_name?: string;
}

export interface PaymentDto {
  id: string;
  order_id: string;
  command_id: string | null;
  cash_register_id: string | null;
  total_amount: number;
  status: 'PENDING' | 'APPROVED' | 'FAILED' | 'REFUNDED';
}

/**
 * Pagamento de autoatendimento do cliente (US-05.4) — sem JWT, autorizado
 * pela secret de QR Code da mesa (a mesma já validada por `useTableAccess`).
 * Nunca aceita `CASH` (validado também no backend).
 *
 * `idempotencyKey`: uma reconexão de rede no celular do cliente sem essa
 * chave criaria um segundo `Payment` aprovado pra mesma comanda — quem
 * chama gera uma chave por sessão do modal de checkout (ver
 * `CustomerCheckoutModal`) e reaproveita em qualquer retry dentro dela.
 */
export async function submitCustomerPayment(
  tenantId: string,
  payload: CustomerCheckoutPayload,
  idempotencyKey: string,
): Promise<PaymentDto> {
  return apiRequest<PaymentDto>(PAYMENT_SERVICE_URL, '/api/v1/payments/customer-checkout', {
    method: 'POST',
    tenantId,
    idempotencyKey,
    body: payload,
  });
}
