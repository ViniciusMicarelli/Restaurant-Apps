import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdminDashboardPage } from './presentation/pages/AdminDashboardPage';
import { LoginPage } from './presentation/pages/LoginPage';
import { useSessionStore } from './infrastructure/state/sessionStore';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1 } },
});

export function App() {
  const isAuthenticated = useSessionStore((state) => state.isAuthenticated);

  return (
    <QueryClientProvider client={queryClient}>
      {isAuthenticated ? <AdminDashboardPage /> : <LoginPage />}
    </QueryClientProvider>
  );
}

export default App;
