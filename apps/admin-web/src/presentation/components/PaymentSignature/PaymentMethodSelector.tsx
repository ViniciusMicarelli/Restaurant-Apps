import React from 'react';

export type CheckoutMethod = 'CREDIT_CARD' | 'DEBIT_CARD' | 'PIX' | 'CASH';

const METHOD_LABELS: Record<CheckoutMethod, string> = {
  CREDIT_CARD: 'Crédito',
  DEBIT_CARD: 'Débito',
  PIX: 'Pix',
  CASH: 'Dinheiro',
};

const METHOD_ORDER: CheckoutMethod[] = ['CREDIT_CARD', 'DEBIT_CARD', 'PIX', 'CASH'];

interface PaymentMethodSelectorProps {
  value: CheckoutMethod;
  onChange: (method: CheckoutMethod) => void;
}

/** Seletor de forma de pagamento do fechamento de comanda — cartão (crédito
 * ou débito) segue pro formulário fake + assinatura de sempre; Pix e Dinheiro
 * têm telas próprias, mais simples (sem assinatura, que não faz sentido pra
 * nenhum dos dois nesse fluxo). */
export const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({ value, onChange }) => (
  <div className="grid grid-cols-4 gap-2 mb-4">
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
