import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getRestaurant,
  updateBranding,
  type UpdateBrandingRequest,
} from '../../infrastructure/api/restaurantApi';
import { useSessionStore } from '../../infrastructure/state/sessionStore';

export function useRestaurant() {
  const tenantId = useSessionStore((state) => state.user?.tenantId);

  return useQuery({
    queryKey: ['restaurant', tenantId],
    queryFn: () => getRestaurant(tenantId!),
    enabled: Boolean(tenantId),
  });
}

export function useUpdateBranding() {
  const tenantId = useSessionStore((state) => state.user?.tenantId);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdateBrandingRequest) => updateBranding(tenantId!, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['restaurant', tenantId] });
    },
  });
}
