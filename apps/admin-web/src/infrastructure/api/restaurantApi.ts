import { apiRequest } from './httpClient';

const RESTAURANT_SERVICE_URL = import.meta.env.VITE_RESTAURANT_SERVICE_URL;

export interface Branding {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color: string;
  surface_color: string;
  theme_mode: string;
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
  legal_name: string;
  cnpj: string;
  phone: string;
  currency: string;
  service_fee_percent: number;
  is_active: boolean;
  branding: Branding;
}

export type UpdateBrandingRequest = Omit<Branding, 'css_variables'>;

export async function getRestaurant(restaurantId: string): Promise<Restaurant> {
  return apiRequest<Restaurant>(RESTAURANT_SERVICE_URL, `/api/v1/restaurants/${restaurantId}`);
}

export async function updateBranding(
  restaurantId: string,
  payload: UpdateBrandingRequest,
): Promise<Restaurant> {
  return apiRequest<Restaurant>(RESTAURANT_SERVICE_URL, `/api/v1/restaurants/${restaurantId}/branding`, {
    method: 'PUT',
    body: payload,
  });
}
