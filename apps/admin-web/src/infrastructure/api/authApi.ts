import { apiRequest } from './httpClient';

const AUTH_SERVICE_URL = import.meta.env.VITE_AUTH_SERVICE_URL;

export interface UserProfile {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_seconds: number;
  user: UserProfile;
}

export async function loginWithPassword(email: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>(AUTH_SERVICE_URL, '/api/v1/auth/login', {
    method: 'POST',
    body: { email, password },
    skipAuth: true,
  });
}
