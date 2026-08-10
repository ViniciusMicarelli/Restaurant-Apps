import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CustomerMenuPage } from './presentation/pages/CustomerMenuPage';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1 } },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CustomerMenuPage />
    </QueryClientProvider>
  );
}

export default App;
