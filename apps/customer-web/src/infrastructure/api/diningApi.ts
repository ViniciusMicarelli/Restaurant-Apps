import { apiRequest } from './httpClient';

const DINING_SERVICE_URL = import.meta.env.VITE_DINING_SERVICE_URL;

export interface ValidateQrSecretResult {
  valid: boolean;
  table_id: string;
}

/**
 * Valida a secret rotativa do QR Code da mesa antes de liberar o cardápio —
 * chamado uma vez no carregamento da página (não a cada request de
 * menu/pedido, ver `resolveTableSecret`).
 */
export async function validateTableQrSecret(
  tenantId: string,
  tableNumber: number,
  secret: string,
): Promise<ValidateQrSecretResult> {
  return apiRequest<ValidateQrSecretResult>(
    DINING_SERVICE_URL,
    `/api/v1/dining/tables/${tableNumber}/qr-secret/validate?secret=${encodeURIComponent(secret)}`,
    { tenantId },
  );
}

export interface CommandDto {
  id: string;
  table_id: string;
  customer_name: string;
  status: 'OPEN' | 'CLOSED';
  service_fee_charged: boolean;
  opened_at: string;
  closed_at: string | null;
}

/**
 * Comanda aberta da mesa atual, pro autoatendimento do cliente (US-05.4) —
 * dá o `command_id`/`service_fee_charged` de que o checkout precisa. Mesma
 * secret já validada por `useTableAccess`.
 */
export async function getOpenCommandForTable(
  tenantId: string,
  tableNumber: number,
  secret: string,
): Promise<CommandDto> {
  return apiRequest<CommandDto>(
    DINING_SERVICE_URL,
    `/api/v1/dining/tables/${tableNumber}/open-command?secret=${encodeURIComponent(secret)}`,
    { tenantId },
  );
}

/**
 * Fecha a própria comanda pelo autoatendimento (US-05.4), depois que o
 * pagamento foi aprovado — libera a mesa pra limpeza igual ao fechamento
 * feito pelo garçom.
 */
export async function customerCloseCommand(
  tenantId: string,
  commandId: string,
  secret: string,
): Promise<CommandDto> {
  return apiRequest<CommandDto>(
    DINING_SERVICE_URL,
    `/api/v1/dining/commands/${commandId}/customer-close?secret=${encodeURIComponent(secret)}`,
    { method: 'POST', tenantId },
  );
}
