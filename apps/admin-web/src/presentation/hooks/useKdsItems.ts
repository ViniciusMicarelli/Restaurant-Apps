import { useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  connectKdsSocket,
  listKdsItems,
  updateKdsItemStatus,
  type KdsItem,
  type KdsItemStatus,
} from '../../infrastructure/api/kitchenApi';
import { useSessionStore } from '../../infrastructure/state/sessionStore';

const KDS_POLL_INTERVAL_MS = 5_000;
const KDS_QUERY_KEY = ['kds-items'];

export function useKdsItems() {
  const accessToken = useSessionStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: KDS_QUERY_KEY,
    queryFn: listKdsItems,
    refetchInterval: KDS_POLL_INTERVAL_MS,
  });

  // WebSocket em tempo real (`/ws/v1/kitchen/kds`) — reduz a latência de
  // "pedido criado"/"status mudou" a quase-instantânea. O polling acima
  // continua como rede de segurança caso o socket caia silenciosamente.
  useEffect(() => {
    if (!accessToken) return;

    return connectKdsSocket(accessToken, ({ item }) => {
      queryClient.setQueryData<KdsItem[]>(KDS_QUERY_KEY, (current) => {
        if (!current) return current;
        const exists = current.some((existing) => existing.id === item.id);
        return exists
          ? current.map((existing) => (existing.id === item.id ? item : existing))
          : [...current, item];
      });
    });
  }, [accessToken, queryClient]);

  return query;
}

export function useUpdateKdsItemStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, newStatus }: { itemId: string; newStatus: KdsItemStatus }) =>
      updateKdsItemStatus(itemId, newStatus),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: KDS_QUERY_KEY });
    },
  });
}
