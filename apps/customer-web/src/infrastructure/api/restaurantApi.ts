import { apiRequest } from './httpClient';

const RESTAURANT_SERVICE_URL = import.meta.env.VITE_RESTAURANT_SERVICE_URL;

export interface Branding {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color: string;
  surface_color: string;
  theme_mode: 'light' | 'dark' | 'auto';
  logo_url: string;
  favicon_url: string;
  banner_url: string;
  font_family: string;
  border_radius: string;
  css_variables: Record<string, string>;
}

export interface Restaurant {
  id: string;
  slug: string;
  trade_name: string;
  currency: string;
  is_active: boolean;
  branding: Branding;
  // Usado pelo checkout do autoatendimento (US-05.4) — mesma fórmula de
  // `apps/admin-web/src/presentation/hooks/useRevenue.ts`.
  service_fee_percent: number;
}

export async function getRestaurantBySlug(slug: string): Promise<Restaurant> {
  return apiRequest<Restaurant>(RESTAURANT_SERVICE_URL, `/api/v1/restaurants/by-slug/${slug}`);
}
