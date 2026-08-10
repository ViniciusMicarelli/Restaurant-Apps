import { afterEach, describe, expect, it } from 'vitest';
import { useSessionStore } from './sessionStore';

afterEach(() => {
  useSessionStore.getState().logout();
});

describe('useSessionStore', () => {
  it('starts unauthenticated', () => {
    expect(useSessionStore.getState().isAuthenticated).toBe(false);
    expect(useSessionStore.getState().user).toBeNull();
  });

  it('login stores the tokens and user, and flips isAuthenticated', () => {
    useSessionStore.getState().login({
      accessToken: 'access-1',
      refreshToken: 'refresh-1',
      user: { id: 'u1', tenantId: 't1', email: 'ana@x.com', name: 'Ana', role: 'MANAGER' },
    });

    const state = useSessionStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.accessToken).toBe('access-1');
    expect(state.user?.name).toBe('Ana');
  });

  it('logout clears the session', () => {
    useSessionStore.getState().login({
      accessToken: 'access-1',
      refreshToken: 'refresh-1',
      user: { id: 'u1', tenantId: 't1', email: 'ana@x.com', name: 'Ana', role: 'MANAGER' },
    });

    useSessionStore.getState().logout();

    const state = useSessionStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.accessToken).toBeNull();
    expect(state.user).toBeNull();
  });
});
