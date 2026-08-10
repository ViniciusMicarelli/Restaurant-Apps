import { useMutation } from '@tanstack/react-query';
import { ApiError } from '../../infrastructure/api/httpClient';
import { loginWithPassword } from '../../infrastructure/api/authApi';
import { useSessionStore } from '../../infrastructure/state/sessionStore';

export function useLogin() {
  const login = useSessionStore((state) => state.login);

  return useMutation<void, ApiError, { email: string; password: string }>({
    mutationFn: async ({ email, password }) => {
      const token = await loginWithPassword(email, password);
      login({
        accessToken: token.access_token,
        refreshToken: token.refresh_token,
        user: {
          id: token.user.id,
          tenantId: token.user.tenant_id,
          email: token.user.email,
          name: token.user.name,
          role: token.user.role,
        },
      });
    },
  });
}
