import { apiRequest } from './httpClient';

const ORDER_SERVICE_URL = import.meta.env.VITE_ORDER_SERVICE_URL;

export type OrderStatus = 'PENDING' | 'PREPARING' | 'READY' | 'DELIVERED' | 'CANCELLED';

export interface OrderItemDto {
  product_id: string;
  product_name: string;
  unit_price: number;
  quantity: number;
  notes: string | null;
  total_price: number;
}

export interface OrderDto {
  id: string;
  table_number: number | null;
  status: OrderStatus;
  items: OrderItemDto[];
  total_amount: number;
  created_at: string;
}

/** Pedidos da mesa — visão "Meu Pedido" do cliente (somente leitura, sem
 * checkout próprio nesta fase; ver docs/TESTING_GUIDE.md). */
export async function listOrdersByTable(tenantId: string, tableNumber: number): Promise<OrderDto[]> {
  return apiRequest<OrderDto[]>(ORDER_SERVICE_URL, `/api/v1/orders?table_number=${tableNumber}`, {
    tenantId,
  });
}
