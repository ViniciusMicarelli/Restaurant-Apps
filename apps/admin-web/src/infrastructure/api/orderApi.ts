import { apiRequest } from './httpClient';

const ORDER_SERVICE_URL = import.meta.env.VITE_ORDER_SERVICE_URL;

export type OrderStatus = 'PENDING' | 'PREPARING' | 'READY' | 'DELIVERED' | 'CANCELLED';

export interface OrderItem {
  product_id: string;
  product_name: string;
  unit_price: number;
  quantity: number;
  notes: string | null;
  total_price: number;
}

export interface Order {
  id: string;
  tenant_id: string;
  order_type: string;
  table_number: number | null;
  command_id: string | null;
  status: OrderStatus;
  items: OrderItem[];
  total_amount: number;
  cancellation_reason: string | null;
  created_at: string;
}

export async function listOrders(params?: { commandId?: string; tableNumber?: number }): Promise<Order[]> {
  const query = new URLSearchParams();
  if (params?.commandId) query.set('command_id', params.commandId);
  if (params?.tableNumber) query.set('table_number', String(params.tableNumber));
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return apiRequest<Order[]>(ORDER_SERVICE_URL, `/api/v1/orders${suffix}`);
}
