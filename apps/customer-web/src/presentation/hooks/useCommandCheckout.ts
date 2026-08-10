import { useMutation, useQuery } from '@tanstack/react-query';
import { customerCloseCommand, getOpenCommandForTable } from '../../infrastructure/api/diningApi';
import {
  submitCustomerPayment,
  type CustomerCheckoutPayload,
  type PaymentDto,
} from '../../infrastructure/api/paymentApi';

/**
 * Comanda aberta da mesa atual — dá o `command_id`/`service_fee_charged`
 * de que o checkout do autoatendimento (US-05.4) precisa. Só habilitada
 * quando o botão "Fechar minha conta" é aberto (não é polling contínuo
 * como `useMyOrders`, evita uma chamada extra a cada 5s à toa).
 */
export function useOpenCommand(
  tenantId: string | undefined,
  tableNumber: number | null,
  secret: string | null,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ['open-command', tenantId, tableNumber, secret],
    queryFn: () => getOpenCommandForTable(tenantId!, tableNumber!, secret!),
    enabled: enabled && Boolean(tenantId && tableNumber && secret),
    retry: false,
  });
}

interface SubmitCheckoutParams {
  commandId: string;
  payload: CustomerCheckoutPayload;
  idempotencyKey: string;
}

/**
 * Paga a comanda e, se aprovado, fecha ela — mesma sequência de duas
 * chamadas do `CheckoutModal` do `admin-web` (paga → fecha), só que pelo
 * canal público do cliente. Se o fechamento falhar porque outro canal (a
 * maquininha do garçom) já fechou a comanda antes, o pagamento já foi
 * processado — o chamador trata esse erro como "sucesso mesmo assim", não
 * como falha (ver `CustomerCheckoutModal`).
 */
export function useSubmitCustomerCheckout(tenantId: string | undefined, secret: string | null) {
  return useMutation<PaymentDto, Error, SubmitCheckoutParams>({
    mutationFn: async ({ commandId, payload, idempotencyKey }) => {
      const payment = await submitCustomerPayment(tenantId!, payload, idempotencyKey);
      try {
        await customerCloseCommand(tenantId!, commandId, secret!);
      } catch {
        // O pagamento já foi aprovado — a comanda pode já ter sido fechada
        // por outro canal (o garçom chegou primeiro com a maquininha).
        // Não propaga como falha: quem chama trata isso como sucesso.
      }
      return payment;
    },
  });
}
