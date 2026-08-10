import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginPage } from './LoginPage';
import { useSessionStore } from '../../infrastructure/state/sessionStore';

function renderWithQueryClient() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <LoginPage />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  useSessionStore.getState().logout();
});

describe('LoginPage', () => {
  it('renders the email and password fields', () => {
    renderWithQueryClient();

    expect(screen.getByPlaceholderText('voce@restaurante.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
  });

  it('logs the user in on successful submit', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: 'access-1',
        refresh_token: 'refresh-1',
        token_type: 'Bearer',
        expires_in_seconds: 900,
        user: { id: 'u1', tenant_id: 't1', email: 'ana@x.com', name: 'Ana', role: 'MANAGER' },
      }),
    });
    vi.stubGlobal('fetch', fetchMock);

    renderWithQueryClient();

    fireEvent.change(screen.getByPlaceholderText('voce@restaurante.com'), {
      target: { value: 'ana@x.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'senha1234' } });
    fireEvent.click(screen.getByRole('button', { name: /entrar/i }));

    await waitFor(() => expect(useSessionStore.getState().isAuthenticated).toBe(true));
    expect(useSessionStore.getState().user?.name).toBe('Ana');
  });

  it('shows the backend error message on failed login', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ title: 'UnauthorizedException', detail: 'Credenciais inválidas.' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    renderWithQueryClient();

    fireEvent.change(screen.getByPlaceholderText('voce@restaurante.com'), {
      target: { value: 'ana@x.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /entrar/i }));

    expect(await screen.findByText('Credenciais inválidas.')).toBeInTheDocument();
    expect(useSessionStore.getState().isAuthenticated).toBe(false);
  });
});
