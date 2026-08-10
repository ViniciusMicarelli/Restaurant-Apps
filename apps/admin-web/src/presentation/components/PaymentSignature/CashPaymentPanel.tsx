import React, { useState } from 'react';

interface CashPaymentPanelProps {
  totalAmount: number;
  isSubmitting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Tela de dinheiro — calcula o troco no cliente (o backend só registra o
 * valor total recebido em `CASH`, que é o que de fato move o saldo do
 * caixa; o troco em si não é um dado que o sistema precisa persistir). */
export const CashPaymentPanel: React.FC<CashPaymentPanelProps> = ({
  totalAmount,
  isSubmitting,
  onConfirm,
  onCancel,
}) => {
  const [received, setReceived] = useState(totalAmount.toFixed(2));
  const receivedNumber = Number(received.replace(',', '.')) || 0;
  const change = Math.max(0, receivedNumber - totalAmount);
  const insufficient = receivedNumber > 0 && receivedNumber < totalAmount;

  return (
    <div className="space-y-4">
      <div>
        <label className="text-xs font-semibold text-gray-700 block mb-1">Valor recebido do cliente</label>
        <input
          inputMode="decimal"
          value={received}
          onChange={(e) => setReceived(e.target.value)}
          className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-sm"
        />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500">Troco</span>
        <span className={`text-lg font-extrabold ${insufficient ? 'text-red-600' : 'text-gray-900'}`}>
          R$ {change.toFixed(2)}
        </span>
      </div>
      {insufficient && (
        <p className="text-[11px] text-red-600">Valor recebido é menor que o total da comanda.</p>
      )}

      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
        <span className="text-xs font-semibold text-gray-500">Total a cobrar</span>
        <span className="text-lg font-extrabold text-gray-900">R$ {totalAmount.toFixed(2)}</span>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 text-xs font-bold text-gray-600 bg-gray-100 hover:bg-gray-200 px-4 py-2.5 rounded-xl"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isSubmitting || insufficient}
          className="flex-1 bg-red-600 disabled:bg-red-300 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-md"
        >
          {isSubmitting ? 'Processando...' : 'Confirmar Pagamento em Dinheiro'}
        </button>
      </div>
    </div>
  );
};
