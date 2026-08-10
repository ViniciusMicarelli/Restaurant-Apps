import { useQuery } from '@tanstack/react-query';
import { getRestaurantBySlug } from '../../infrastructure/api/restaurantApi';
import { resolveRestaurantSlug } from '../../infrastructure/restaurantSlug';

export function useRestaurant() {
  const slug = resolveRestaurantSlug();

  return useQuery({
    queryKey: ['restaurant', slug],
    queryFn: () => getRestaurantBySlug(slug!),
    enabled: Boolean(slug),
  });
}
