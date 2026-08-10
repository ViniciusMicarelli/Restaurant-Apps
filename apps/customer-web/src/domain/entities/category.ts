/**
 * Entidade de Domínio de Categoria no Frontend (DDD).
 *
 * Espelha `CategoryResponse` do `menu-service`. `icon` é decoração puramente
 * de UI (o backend não modela ícone de categoria) — sempre preenchido no
 * mapeamento da API para um valor padrão.
 */

export interface Category {
  id: string;
  name: string;
  icon: string;
  display_order: number;
}
