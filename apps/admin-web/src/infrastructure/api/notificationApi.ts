import { apiRequest } from './httpClient';

const NOTIFICATION_SERVICE_URL = import.meta.env.VITE_NOTIFICATION_SERVICE_URL;

export type NotificationChannel = 'EMAIL' | 'WHATSAPP' | 'PUSH' | 'IN_APP';
export type NotificationStatus = 'QUEUED' | 'SENT' | 'FAILED';

export interface Notification {
  id: string;
  tenant_id: string;
  channel: NotificationChannel;
  recipient: string;
  template_code: string;
  rendered_body: string;
  context: Record<string, string>;
  status: NotificationStatus;
  error_message: string | null;
  created_at: string;
}

export async function listNotifications(): Promise<Notification[]> {
  return apiRequest<Notification[]>(NOTIFICATION_SERVICE_URL, '/api/v1/notifications');
}
