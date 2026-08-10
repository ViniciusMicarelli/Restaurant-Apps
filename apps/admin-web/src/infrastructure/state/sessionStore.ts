/**
 * Estado de sessão (autenticação/tenant) persistido em `localStorage`.
 *
 * Único lugar da aplicação que guarda o par de tokens JWT — todo cliente
 * HTTP lê o `accessToken` daqui (ver `infrastructure/api/httpClient.ts`).
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface SessionUser {
  id: string;
  tenantId: string;
  email: string;
  name: string;
  role: string;
}

interface SessionState {
  accessToken: string | null;
  refreshToken: string | null;
  user: SessionUser | null;
  isAuthenticated: boolean;
  login: (params: { accessToken: string; refreshToken: string; user: SessionUser }) => void;
  logout: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      login: ({ accessToken, refreshToken, user }) =>
        set({ accessToken, refreshToken, user, isAuthenticated: true }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false }),
    }),
    { name: 'admin-web-session' },
  ),
);
