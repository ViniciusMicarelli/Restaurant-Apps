import { apiRequest } from './httpClient';

const KITCHEN_SERVICE_URL = import.meta.env.VITE_KITCHEN_SERVICE_URL;
const KITCHEN_WS_URL = import.meta.env.VITE_KITCHEN_WS_URL;

export type KdsItemStatus = 'PENDING' | 'PREPARING' | 'READY' | 'DELIVERED';
export type KdsStation = 'COZINHA_QUENTE' | 'BAR' | 'SOBREMESAS' | 'OUTROS';

export interface KdsItem {
  id: string;
  tenant_id: string;
  order_id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  station: KdsStation;
  table_number: number | null;
  notes: string | null;
  status: KdsItemStatus;
  created_at: string;
  ready_at: string | null;
  delivered_at: string | null;
}

export async function listKdsItems(): Promise<KdsItem[]> {
  return apiRequest<KdsItem[]>(KITCHEN_SERVICE_URL, '/api/v1/kitchen/kds/items');
}

export async function updateKdsItemStatus(itemId: string, newStatus: KdsItemStatus): Promise<KdsItem> {
  return apiRequest<KdsItem>(KITCHEN_SERVICE_URL, `/api/v1/kitchen/kds/items/${itemId}/status`, {
    method: 'PATCH',
    body: { new_status: newStatus },
  });
}

export type KdsItemSocketEvent =
  | { event: 'KDS_ITEM_CREATED'; item: KdsItem }
  | { event: 'KDS_ITEM_STATUS_CHANGED'; item: KdsItem };

export type KdsSocketEvent = KdsItemSocketEvent | { event: 'PONG'; payload: string };

/**
 * Abre o WebSocket em tempo real do KDS (`kitchen-service`), autenticado via
 * `?token=<access_token>` na query string (mesmo padrão do backend —
 * `kds_websocket_endpoint`, só aceita RESTAURANT_OWNER/MANAGER/KITCHEN_STAFF).
 * Reconecta com backoff simples se a conexão cair; `onMessage` é chamado a
 * cada evento `KDS_ITEM_CREATED`/`KDS_ITEM_STATUS_CHANGED` recebido.
 *
 * Retorna uma função de limpeza que fecha o socket e cancela reconexões.
 */
export function connectKdsSocket(
  accessToken: string,
  onMessage: (event: KdsItemSocketEvent) => void,
): () => void {
  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let closedByCaller = false;

  const connect = () => {
    socket = new WebSocket(`${KITCHEN_WS_URL}?token=${encodeURIComponent(accessToken)}`);

    socket.onmessage = (raw) => {
      try {
        const parsed = JSON.parse(raw.data) as KdsSocketEvent;
        if (parsed.event === 'KDS_ITEM_CREATED' || parsed.event === 'KDS_ITEM_STATUS_CHANGED') {
          onMessage(parsed);
        }
      } catch {
        // mensagem não-JSON (não deveria acontecer) — ignora.
      }
    };

    socket.onclose = () => {
      if (!closedByCaller) {
        reconnectTimer = setTimeout(connect, 3_000);
      }
    };
  };

  connect();

  return () => {
    closedByCaller = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    socket?.close();
  };
}
