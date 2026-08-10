import { useQuery } from '@tanstack/react-query';
import { listOrders } from '../../infrastructure/api/orderApi';

const ORDERS_POLL_INTERVAL_MS = 5_000;

export function useOrdersByCommand(commandId: string | undefined) {
  return useQuery({
    queryKey: ['orders', 'by-command', commandId],
    queryFn: () => listOrders({ commandId }),
    enabled: Boolean(commandId),
    refetchInterval: ORDERS_POLL_INTERVAL_MS,
  });
}
