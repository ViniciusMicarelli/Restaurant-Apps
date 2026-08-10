/**
 * Entidade de Domínio de Produto no Frontend (DDD).
 *
 * Espelha `ProductResponse` do `menu-service` — sem campos fabricados no
 * cliente (nota, nº de avaliações, preço "de/por") que o backend não expõe.
 */

export interface Product {
  id: string;
  category_id: string;
  name: string;
  description: string;
  price: number;
  photo_url: string;
  is_active: boolean;
}
