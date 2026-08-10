import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CustomerCardForm } from './CustomerCardForm';

describe('CustomerCardForm', () => {
  it('keeps the submit button disabled until every field is valid', () => {
    render(
      <CustomerCardForm totalAmount={50} isSubmitting={false} onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(screen.getByRole('button', { name: /pagar agora/i })).toBeDisabled();
  });

  it('calls onSubmit with only the last 4 digits and holder name once valid', () => {
    const onSubmit = vi.fn();
    render(
      <CustomerCardForm totalAmount={50} isSubmitting={false} onSubmit={onSubmit} onCancel={vi.fn()} />,
    );

    fireEvent.change(screen.getByPlaceholderText('1234 5678 9012 3456'), {
      target: { value: '4111111111111111' },
    });
    fireEvent.change(screen.getByPlaceholderText('NOME COMPLETO'), { target: { value: 'Lucas Silva' } });
    const [monthSelect, yearSelect] = screen.getAllByRole('combobox');
    fireEvent.change(monthSelect, { target: { value: '12' } });
    fireEvent.change(yearSelect, { target: { value: String(new Date().getFullYear() + 1) } });
    fireEvent.change(screen.getByPlaceholderText('***'), { target: { value: '123' } });

    const submitButton = screen.getByRole('button', { name: /pagar agora/i });
    expect(submitButton).toBeEnabled();
    fireEvent.click(submitButton);

    // O campo de titular normaliza pra maiúsculas (mesmo comportamento do
    // PaymentSignatureForm do admin-web) — o valor digitado foi "Lucas Silva".
    expect(onSubmit).toHaveBeenCalledWith({ cardLast4: '1111', cardHolderName: 'LUCAS SILVA' });
  });

  it('never renders a field for the client-side signature', () => {
    render(
      <CustomerCardForm totalAmount={50} isSubmitting={false} onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(screen.queryByText(/assinatura/i)).not.toBeInTheDocument();
  });
});
