import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CustomerCheckoutModal } from './CustomerCheckoutModal';
import type { OrderDto } from '../../../infrastructure/api/orderApi';

const useOpenCommandMock = vi.fn();
const useSubmitCustomerCheckoutMock = vi.fn();
const mutateMock = vi.fn();

vi.mock('../../hooks/useCommandCheckout', () => ({
  useOpenCommand: (...args: unknown[]) => useOpenCommandMock(...args),
  useSubmitCustomerCheckout: (...args: unknown[]) => useSubmitCustomerCheckoutMock(...args),
}));

// Evita depender do WASM/canvas real do @rive-app/react-canvas em jsdom —
// não é o que este teste está verificando.
vi.mock('../Rive/RiveLoadingIndicator', () => ({
  RiveLoadingIndicator: () => <div data-testid="rive-loading" />,
}));
vi.mock('../Rive/OrderReadyCelebration', () => ({
  OrderReadyCelebration: ({ message }: { message: string }) => (
    <div data-testid="celebration">{message}</div>
  ),
}));

const orders: OrderDto[] = [
  {
    id: 'order-1',
    table_number: 5,
    status: 'DELIVERED',
    items: [],
    total_amount: 50,
    created_at: '2026-01-01T00:00:00Z',
  },
];

function renderModal() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <CustomerCheckoutModal
        tenantId="tenant-1"
        tableNumber={5}
        secret="secret-1"
        orders={orders}
        serviceFeePercent={10}
        onClose={vi.fn()}
        onPaid={vi.fn()}
      />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  mutateMock.mockReset();
  useOpenCommandMock.mockReset();
  useSubmitCustomerCheckoutMock.mockReset();
  useSubmitCustomerCheckoutMock.mockReturnValue({ mutate: mutateMock, isPending: false, isError: false });
});

describe('CustomerCheckoutModal', () => {
  it('shows a friendly message instead of a raw error when there is no open command', () => {
    useOpenCommandMock.mockReturnValue({ isLoading: false, isError: true, data: undefined });

    renderModal();

    expect(screen.getByText(/não encontramos uma comanda aberta/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /pagar agora/i })).not.toBeInTheDocument();
  });

  it('shows a loading state while the open command is being fetched', () => {
    useOpenCommandMock.mockReturnValue({ isLoading: true, isError: false, data: undefined });

    renderModal();

    expect(screen.getByTestId('rive-loading')).toBeInTheDocument();
  });

  it('submits a card payment with the total including the service fee', () => {
    useOpenCommandMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { id: 'command-1', status: 'OPEN', service_fee_charged: true },
    });

    renderModal();

    fireEvent.change(screen.getByPlaceholderText('1234 5678 9012 3456'), {
      target: { value: '4111111111111111' },
    });
    fireEvent.change(screen.getByPlaceholderText('NOME COMPLETO'), { target: { value: 'Lucas' } });
    const [monthSelect, yearSelect] = screen.getAllByRole('combobox');
    fireEvent.change(monthSelect, { target: { value: '12' } });
    fireEvent.change(yearSelect, { target: { value: String(new Date().getFullYear() + 1) } });
    fireEvent.change(screen.getByPlaceholderText('***'), { target: { value: '123' } });

    fireEvent.click(screen.getByRole('button', { name: /pagar agora/i }));

    expect(mutateMock).toHaveBeenCalledWith(
      expect.objectContaining({
        commandId: 'command-1',
        payload: expect.objectContaining({
          table_number: 5,
          secret: 'secret-1',
          // splits[0].amount usa a mesma fórmula do servidor (50 * 1.10)
          // pra bater com o total real — mas quem decide se aprova é o
          // servidor, não este valor. order_id/command_id/expected_total
          // NUNCA vão no payload (revisão de segurança, 2026-08-10).
          splits: [{ payment_method: 'CREDIT_CARD', amount: 55 }],
        }),
      }),
      expect.any(Object),
    );
    const [sentArgs] = mutateMock.mock.calls[0];
    expect(sentArgs.payload).not.toHaveProperty('order_id');
    expect(sentArgs.payload).not.toHaveProperty('command_id');
    expect(sentArgs.payload).not.toHaveProperty('expected_total');
  });

  it('does not charge the service fee when the command has not marked it as charged', () => {
    useOpenCommandMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { id: 'command-1', status: 'OPEN', service_fee_charged: false },
    });

    renderModal();

    // Troca pro Pix, que não exige preencher formulário nenhum.
    fireEvent.click(screen.getByRole('button', { name: 'Pix' }));
    fireEvent.click(screen.getByRole('button', { name: /já paguei pelo pix/i }));

    expect(mutateMock).toHaveBeenCalledWith(
      expect.objectContaining({
        payload: expect.objectContaining({ splits: [{ payment_method: 'PIX', amount: 50 }] }),
      }),
      expect.any(Object),
    );
  });

  it('excludes cancelled orders from the total sent, matching the server calculation', () => {
    useOpenCommandMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { id: 'command-1', status: 'OPEN', service_fee_charged: false },
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <CustomerCheckoutModal
          tenantId="tenant-1"
          tableNumber={5}
          secret="secret-1"
          orders={[
            ...orders,
            {
              id: 'order-2',
              table_number: 5,
              status: 'CANCELLED',
              items: [],
              total_amount: 999,
              created_at: '2026-01-01T00:00:00Z',
            },
          ]}
          serviceFeePercent={10}
          onClose={vi.fn()}
          onPaid={vi.fn()}
        />
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Pix' }));
    fireEvent.click(screen.getByRole('button', { name: /já paguei pelo pix/i }));

    expect(mutateMock).toHaveBeenCalledWith(
      expect.objectContaining({
        payload: expect.objectContaining({ splits: [{ payment_method: 'PIX', amount: 50 }] }),
      }),
      expect.any(Object),
    );
  });
});
