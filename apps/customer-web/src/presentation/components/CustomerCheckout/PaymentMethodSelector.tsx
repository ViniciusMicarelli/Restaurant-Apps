import React from 'react';

export type CustomerCheckoutMethod = 'CREDIT_CARD' | 'DEBIT_CARD' | 'PIX';

const METHOD_LABELS: Record<CustomerCheckoutMethod, string> = {
  CREDIT_CARD: 'Crédito',
  DEBIT_CARD: 'Débito',
  PIX: 'Pix',
};

const METHOD_ORDER: CustomerCheckoutMethod[] = ['CREDIT_CARD', 'DEBIT_CARD', 'PIX'];

interface PaymentMethodSelectorProps {
  value: CustomerCheckoutMethod;
  onChange: (method: CustomerCheckoutMethod) => void;
}

/**
 * Seletor de forma de pagamento do autoatendimento (US-05.4) — só
 * Cartão/Pix (sem Dinheiro, que não faz sentido num pagamento remoto pelo
 * próprio celular do cliente). Mesmo visual do `PaymentMethodSelector` do
 * `admin-web`, com um conjunto de opções menor — cada app mantém sua
 * própria cópia (não há pacote de componentes React compartilhado entre
 * `admin-web`/`customer-web` neste projeto).
 */
export const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({ value, onChange }) => (
  <div className="grid grid-cols-3 gap-2 mb-4">
    {METHOD_ORDER.map((method) => (
      <button
        key={method}
        type="button"
        onClick={() => onChange(method)}
        className={`text-[11px] font-bold py-2 rounded-xl border transition-colors ${
          value === method
            ? 'bg-gray-900 text-white border-gray-900'
            : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
        }`}
      >
        {METHOD_LABELS[method]}
      </button>
    ))}
  </div>
);
