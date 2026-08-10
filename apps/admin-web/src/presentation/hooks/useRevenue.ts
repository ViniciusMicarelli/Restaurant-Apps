import { useQuery } from '@tanstack/react-query';
import { listPayments, type Payment } from '../../infrastructure/api/paymentApi';
import { listCommands, type Command } from '../../infrastructure/api/diningApi';
import { listOrders } from '../../infrastructure/api/orderApi';

const REVENUE_POLL_INTERVAL_MS = 10_000;

export interface PaymentHistoryEntry {
  payment: Payment;
  tableNumber: number | null;
}

export interface RevenueSummary {
  totalRevenue: number;
  paymentsCount: number;
  closedCommandsCount: number;
  /** Comandas fechadas com taxa de serviço marcada, com o total de pedidos de
   * cada uma — a % em si (`restaurant.service_fee_percent`) é aplicada pelo
   * componente, que já tem esse dado carregado via `useRestaurant()`. */
  closedCommandsWithFee: { command: Command; ordersTotal: number }[];
  /** Histórico de pagamentos aprovados, mais recente primeiro — mesa
   * resolvida via `command_id` quando presente ("Payment por Comanda", mais
   * confiável numa comanda com vários pedidos), com fallback pra `order_id`
   * em pagamentos antigos que não têm `command_id` (o `payment-service` não
   * guarda o número da mesa diretamente, só referencia comanda/pedido). */
  paymentHistory: PaymentHistoryEntry[];
}

/**
 * Agregação de faturamento — feita no cliente combinando 3 serviços
 * (payment-service, dining-service, order-service), já que não existe (nem
 * é necessário para este porte) um serviço de relatórios dedicado:
 * `analytics-service` hoje só tem `AuditLog`, sem agregação de vendas.
 */
export function useRevenue() {
  return useQuery<RevenueSummary>({
    queryKey: ['revenue'],
    queryFn: async () => {
      const [payments, closedCommands, allOrders] = await Promise.all([
        listPayments('APPROVED'),
        listCommands('CLOSED'),
        listOrders(),
      ]);

      const totalRevenue = payments.reduce((sum, p) => sum + p.total_amount, 0);
      const feeCommands = closedCommands.filter((c) => c.service_fee_charged);
      const closedCommandsWithFee = await Promise.all(
        feeCommands.map(async (command) => {
          const orders = await listOrders({ commandId: command.id });
          const ordersTotal = orders.reduce((sum, o) => sum + o.total_amount, 0);
          return { command, ordersTotal };
        }),
      );

      const tableNumberByOrderId = new Map(allOrders.map((o) => [o.id, o.table_number]));
      const tableNumberByCommandId = new Map(
        allOrders.filter((o) => o.command_id).map((o) => [o.command_id as string, o.table_number]),
      );
      const paymentHistory: PaymentHistoryEntry[] = [...payments]
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .map((payment) => ({
          payment,
          tableNumber: payment.command_id
            ? (tableNumberByCommandId.get(payment.command_id) ?? null)
            : (tableNumberByOrderId.get(payment.order_id) ?? null),
        }));

      return {
        totalRevenue,
        paymentsCount: payments.length,
        closedCommandsCount: closedCommands.length,
        closedCommandsWithFee,
        paymentHistory,
      };
    },
    refetchInterval: REVENUE_POLL_INTERVAL_MS,
  });
}
