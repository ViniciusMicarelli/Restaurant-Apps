/**
 * Resolve o slug do restaurante a partir da URL (`?r=<slug>`) — é assim que
 * o QR Code de cada mesa aponta para o cardápio digital do restaurante
 * correto (docs/modules/module_breakdown.md §3). Cai para
 * `VITE_DEFAULT_RESTAURANT_SLUG` (ambiente de desenvolvimento/demo) quando
 * a URL não traz o parâmetro.
 */
export function resolveRestaurantSlug(): string | null {
  const fromUrl = new URLSearchParams(window.location.search).get('r');
  return fromUrl ?? import.meta.env.VITE_DEFAULT_RESTAURANT_SLUG ?? null;
}

/** Número da mesa, se o QR Code também o informar (`?table=12`). */
export function resolveTableNumber(): number | null {
  const raw = new URLSearchParams(window.location.search).get('table');
  const parsed = raw ? Number(raw) : NaN;
  return Number.isFinite(parsed) ? parsed : null;
}

/**
 * Secret rotativa do QR Code da mesa (`?secret=...`) — obrigatória desde que
 * o cardápio digital passou a exigir validação por mesa (sem fallback: ao
 * contrário do slug, uma secret não tem um valor-padrão sensato de dev).
 */
export function resolveTableSecret(): string | null {
  return new URLSearchParams(window.location.search).get('secret');
}
