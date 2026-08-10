import { apiRequest } from './httpClient';

const MENU_SERVICE_URL = import.meta.env.VITE_MENU_SERVICE_URL;

export interface CategoryDto {
  id: string;
  tenant_id: string;
  name: string;
  display_order: number;
  is_active: boolean;
}

export interface ProductDto {
  id: string;
  tenant_id: string;
  category_id: string;
  name: string;
  description: string;
  price: number;
  cost_price: number;
  tax_rate: number;
  photo_url: string;
  display_order: number;
  is_active: boolean;
}

export async function listCategories(tenantId: string): Promise<CategoryDto[]> {
  return apiRequest<CategoryDto[]>(MENU_SERVICE_URL, '/api/v1/menu/categories', { tenantId });
}

export async function listProducts(tenantId: string): Promise<ProductDto[]> {
  return apiRequest<ProductDto[]>(MENU_SERVICE_URL, '/api/v1/menu/products', { tenantId });
}
