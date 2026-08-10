import { describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import { CustomerPixPanel } from './CustomerPixPanel';

vi.mock('qrcode', () => ({
  default: { toDataURL: vi.fn().mockResolvedValue('data:image/png;base64,fake') },
}));

describe('CustomerPixPanel', () => {
  it('calls onConfirm when the customer confirms the Pix payment, without asking for a signature', async () => {
    const onConfirm = vi.fn();
    await act(async () => {
      render(
        <CustomerPixPanel totalAmount={50} isSubmitting={false} onConfirm={onConfirm} onCancel={vi.fn()} />,
      );
    });

    screen.getByRole('button', { name: /já paguei pelo pix/i }).click();

    expect(onConfirm).toHaveBeenCalled();
    expect(screen.queryByText(/assinatura/i)).not.toBeInTheDocument();
  });

  it('shows the total amount to pay', async () => {
    await act(async () => {
      render(
        <CustomerPixPanel totalAmount={123.45} isSubmitting={false} onConfirm={vi.fn()} onCancel={vi.fn()} />,
      );
    });

    expect(screen.getByText('R$ 123.45')).toBeInTheDocument();
  });
});
