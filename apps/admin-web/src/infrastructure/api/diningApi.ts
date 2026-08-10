import { apiRequest } from './httpClient';

const DINING_SERVICE_URL = import.meta.env.VITE_DINING_SERVICE_URL;

export type TableStatus = 'AVAILABLE' | 'OCCUPIED' | 'RESERVED' | 'WAITING_CLEANING';
export type CommandStatus = 'OPEN' | 'CLOSED';

export interface Table {
  id: string;
  tenant_id: string;
  number: number;
  capacity: number;
  status: TableStatus;
  qr_code_url: string;
}

export interface Command {
  id: string;
  tenant_id: string;
  table_id: string;
  customer_name: string;
  customer_cpf: string | null;
  waiter_id: string;
  status: CommandStatus;
  service_fee_charged: boolean;
  opened_at: string;
  closed_at: string | null;
}

export interface CreateTableRequest {
  number: number;
  capacity: number;
  qr_code_url?: string;
}

export async function listTables(): Promise<Table[]> {
  return apiRequest<Table[]>(DINING_SERVICE_URL, '/api/v1/dining/tables');
}

/** Libera uma mesa "Aguardando Limpeza" de volta pra disponível (US-03.5) —
 * sem isso, toda comanda encerrada prende a mesa pra sempre. */
export async function markTableCleaned(tableId: string): Promise<Table> {
  return apiRequest<Table>(DINING_SERVICE_URL, `/api/v1/dining/tables/${tableId}/mark-cleaned`, {
    method: 'POST',
  });
}

export async function createTable(payload: CreateTableRequest): Promise<Table> {
  return apiRequest<Table>(DINING_SERVICE_URL, '/api/v1/dining/tables', {
    method: 'POST',
    body: { qr_code_url: '', ...payload },
  });
}

export async function listCommands(status?: CommandStatus): Promise<Command[]> {
  const suffix = status ? `?status=${status}` : '';
  return apiRequest<Command[]>(DINING_SERVICE_URL, `/api/v1/dining/commands${suffix}`);
}

export async function setCommandServiceFee(commandId: string, charged: boolean): Promise<Command> {
  return apiRequest<Command>(DINING_SERVICE_URL, `/api/v1/dining/commands/${commandId}/service-fee`, {
    method: 'PATCH',
    body: { charged },
  });
}

export async function closeCommand(commandId: string): Promise<Command> {
  return apiRequest<Command>(DINING_SERVICE_URL, `/api/v1/dining/commands/${commandId}/close`, {
    method: 'POST',
  });
}

export interface TableQrSecret {
  secret: string;
  expires_at: string;
}

export async function rotateTableQrSecret(tableId: string): Promise<TableQrSecret> {
  return apiRequest<TableQrSecret>(DINING_SERVICE_URL, `/api/v1/dining/tables/${tableId}/qr-secret/rotate`, {
    method: 'POST',
  });
}
