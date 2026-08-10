import { useQuery } from '@tanstack/react-query';
import { listNotifications } from '../../infrastructure/api/notificationApi';

const NOTIFICATIONS_POLL_INTERVAL_MS = 5_000;

export function useNotifications() {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: listNotifications,
    refetchInterval: NOTIFICATIONS_POLL_INTERVAL_MS,
  });
}
