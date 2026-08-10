/**
 * Gerenciador de Injeção Dinâmica de Tema e Branding White-Label.
 * 
 * Permite que cada restaurante configure suas próprias cores, logo e banner
 * salvos no banco de dados (restaurante-service), injetando variáveis CSS
 * em tempo de execução para os frontends Web e Apps Mobile.
 */

export interface RestaurantBranding {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color: string;
  surface_color: string;
  theme_mode: 'light' | 'dark' | 'auto';
  logo_url: string;
  banner_url: string;
  font_family: string;
}

export const defaultBranding: RestaurantBranding = {
  primary_color: '#EA1D2C', // iFood Red Style
  secondary_color: '#1E293B',
  accent_color: '#059669', // Emerald Green
  background_color: '#F8FAFC',
  surface_color: '#FFFFFF',
  theme_mode: 'light',
  logo_url: 'https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=300&q=80',
  banner_url: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80',
  font_family: 'Inter',
};

export function applyBrandingToDOM(branding: RestaurantBranding = defaultBranding): void {
  const root = document.documentElement;

  root.style.setProperty('--brand-primary', branding.primary_color);
  root.style.setProperty('--brand-secondary', branding.secondary_color);
  root.style.setProperty('--brand-accent', branding.accent_color);
  root.style.setProperty('--brand-bg', branding.background_color);
  root.style.setProperty('--brand-surface', branding.surface_color);
  root.style.setProperty('--font-family', `'${branding.font_family}', sans-serif`);
}
