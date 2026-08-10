import { useQuery } from '@tanstack/react-query';
import { listOrdersByTable } from '../../infrastructure/api/orderApi';

const MY_ORDERS_POLL_INTERVAL_MS = 5_000;

export function useMyOrders(
  tenantId: string | undefined,
  tableNumber: number | null,
  enabled = true,
) {
  return useQuery({
    queryKey: ['my-orders', tenantId, tableNumber],
    queryFn: () => listOrdersByTable(tenantId!, tableNumber!),
    enabled: enabled && Boolean(tenantId && tableNumber),
    refetchInterval: MY_ORDERS_POLL_INTERVAL_MS,
  });
}
