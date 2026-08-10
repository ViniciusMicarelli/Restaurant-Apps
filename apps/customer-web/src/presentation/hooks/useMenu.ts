import { useQuery } from '@tanstack/react-query';
import { listCategories, listProducts } from '../../infrastructure/api/menuApi';
import type { Category } from '../../domain/entities/category';
import type { Product } from '../../domain/entities/product';

const DEFAULT_CATEGORY_ICON = '🍽️';

export function useCategories(tenantId: string | undefined) {
  return useQuery({
    queryKey: ['menu', 'categories', tenantId],
    queryFn: async (): Promise<Category[]> => {
      const categories = await listCategories(tenantId!);
      return categories
        .filter((c) => c.is_active)
        .sort((a, b) => a.display_order - b.display_order)
        .map((c) => ({
          id: c.id,
          name: c.name,
          icon: DEFAULT_CATEGORY_ICON,
          display_order: c.display_order,
        }));
    },
    enabled: Boolean(tenantId),
  });
}

export function useProducts(tenantId: string | undefined) {
  return useQuery({
    queryKey: ['menu', 'products', tenantId],
    queryFn: async (): Promise<Product[]> => {
      const products = await listProducts(tenantId!);
      return products
        .filter((p) => p.is_active)
        .map((p) => ({
          id: p.id,
          category_id: p.category_id,
          name: p.name,
          description: p.description,
          price: p.price,
          photo_url: p.photo_url,
          is_active: p.is_active,
        }));
    },
    enabled: Boolean(tenantId),
  });
}
