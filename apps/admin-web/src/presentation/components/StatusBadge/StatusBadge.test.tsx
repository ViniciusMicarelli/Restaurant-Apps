import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusPill, statusStripeClassName } from './StatusBadge';

describe('StatusPill', () => {
  it('renders the label', () => {
    render(<StatusPill tone="accent" label="Ocupada" />);

    expect(screen.getByText('Ocupada')).toBeInTheDocument();
  });

  it('uses a different tone class per status, so states never rely on text alone', () => {
    const { rerender } = render(<StatusPill tone="good" label="Livre" />);
    expect(screen.getByText('Livre').closest('span')).toHaveClass('bg-good-soft', 'text-good');

    rerender(<StatusPill tone="critical" label="Atrasado" />);
    expect(screen.getByText('Atrasado').closest('span')).toHaveClass('bg-critical-soft', 'text-critical');
  });
});

describe('statusStripeClassName', () => {
  it('returns a distinct stripe color per tone', () => {
    expect(statusStripeClassName('good')).toContain('before:bg-good');
    expect(statusStripeClassName('accent')).toContain('before:bg-accent');
    expect(statusStripeClassName('warning')).toContain('before:bg-warning');
    expect(statusStripeClassName('critical')).toContain('before:bg-critical');
    expect(statusStripeClassName('info')).toContain('before:bg-info');
  });
});
