import { apiRequest } from './httpClient';

const PAYMENT_SERVICE_URL = import.meta.env.VITE_PAYMENT_SERVICE_URL;

export type PaymentStatus = 'PENDING' | 'APPROVED' | 'FAILED' | 'REFUNDED';
export type PaymentMethod = 'CREDIT_CARD' | 'DEBIT_CARD' | 'PIX' | 'CASH' | 'VOUCHER';

export interface CashRegister {
  id: string;
  tenant_id: string;
  operator_id: string;
  opening_amount: number;
  current_balance: number;
  status: 'OPEN' | 'CLOSED';
  opened_at: string;
  closed_at: string | null;
  closing_counted_amount: number | null;
  closing_divergence: number | null;
}

export interface PaymentSplit {
  payment_method: PaymentMethod;
  amount: number;
}

export interface Payment {
  id: string;
  tenant_id: string;
  order_id: string;
  cash_register_id: string;
  /** Referência autoritativa da comanda paga ("Payment por Comanda") —
   * `null` em pagamentos de pedido avulso e em registros anteriores a esta
   * coluna (ver `useRevenue.ts` para o fallback via `order_id`). */
  command_id: string | null;
  splits: PaymentSplit[];
  total_amount: number;
  status: PaymentStatus;
  card_last4: string | null;
  card_holder_name: string | null;
  signature_data: string | null;
  created_at: string;
}

export interface ProcessPaymentRequest {
  order_id: string;
  cash_register_id: string;
  command_id?: string;
  expected_total: number;
  splits: PaymentSplit[];
  card_last4?: string;
  card_holder_name?: string;
  signature_data?: string;
}

export interface OpenCashRegisterRequest {
  operator_id: string;
  opening_amount: number;
}

export async function getMyOpenCashRegister(): Promise<CashRegister | null> {
  return apiRequest<CashRegister | null>(PAYMENT_SERVICE_URL, '/api/v1/payments/cash-registers/mine');
}

/** Abre o caixa do próprio operador logado — fluxo do garçom que cobra na
 * mesa com a maquininha (cartão) não tem valor físico em dinheiro pra
 * suprimento inicial, por isso `opening_amount` costuma ser `0`. */
export async function openCashRegister(payload: OpenCashRegisterRequest): Promise<CashRegister> {
  return apiRequest<CashRegister>(PAYMENT_SERVICE_URL, '/api/v1/payments/cash-registers', {
    method: 'POST',
    body: payload,
  });
}

/**
 * `idempotencyKey`: sem ela, um retry de rede (comum na maquininha/celular
 * do garçom) duplica o `Payment` — quem chama gera uma chave por sessão do
 * `CheckoutModal` e reaproveita em qualquer retry dentro dela.
 */
export async function processPayment(
  payload: ProcessPaymentRequest,
  idempotencyKey: string,
): Promise<Payment> {
  return apiRequest<Payment>(PAYMENT_SERVICE_URL, '/api/v1/payments', {
    method: 'POST',
    body: payload,
    headers: { 'Idempotency-Key': idempotencyKey },
  });
}

export async function listPayments(status?: PaymentStatus): Promise<Payment[]> {
  const suffix = status ? `?status=${status}` : '';
  return apiRequest<Payment[]>(PAYMENT_SERVICE_URL, `/api/v1/payments${suffix}`);
}
