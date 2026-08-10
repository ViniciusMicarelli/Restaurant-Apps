import React, { useState } from 'react';
import { PenLine, X } from 'lucide-react';
import type { Payment, PaymentMethod } from '../../../infrastructure/api/paymentApi';
import type { PaymentHistoryEntry } from '../../hooks/useRevenue';

const METHOD_LABELS: Record<PaymentMethod, string> = {
  CREDIT_CARD: 'Crédito',
  DEBIT_CARD: 'Débito',
  PIX: 'Pix',
  CASH: 'Dinheiro',
  VOUCHER: 'Voucher',
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

const SignatureModal: React.FC<{ payment: Payment; onClose: () => void }> = ({ payment, onClose }) => (
  <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50">
    <div className="bg-surface rounded-2xl shadow-2xl w-full max-w-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-bold font-display text-ink">Assinatura do Cliente</h4>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-paper text-ink-soft">
          <X className="w-4 h-4" />
        </button>
      </div>
      {payment.card_holder_name && (
        <p className="text-xs text-ink-soft mb-2">Titular: {payment.card_holder_name}</p>
      )}
      {payment.signature_data ? (
        <img
          src={payment.signature_data}
          alt={`Assinatura de ${payment.card_holder_name ?? 'cliente'}`}
          className="w-full bg-paper rounded-xl border border-border"
        />
      ) : (
        <p className="text-xs text-ink-soft">Este pagamento não tem assinatura registrada.</p>
      )}
    </div>
  </div>
);

/**
 * Histórico de pagamentos aprovados — data, mesa, forma de pagamento e valor
 * de cada transação, com acesso à assinatura capturada no fechamento (quando
 * o método foi cartão; Pix/Dinheiro não coletam assinatura).
 */
export const PaymentHistoryTable: React.FC<{ entries: PaymentHistoryEntry[] }> = ({ entries }) => {
  const [viewingSignatureOf, setViewingSignatureOf] = useState<Payment | null>(null);

  if (entries.length === 0) {
    return (
      <div className="bg-surface rounded-xl border border-border shadow-sm p-4">
        <p className="text-xs text-ink-soft">Nenhum pagamento aprovado ainda.</p>
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-xl border border-border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-border">
        <span className="text-xs font-bold font-display text-ink">Histórico de Pagamentos</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-ink-soft border-b border-border">
              <th className="px-4 py-2 font-semibold">Data/Hora</th>
              <th className="px-4 py-2 font-semibold">Mesa</th>
              <th className="px-4 py-2 font-semibold">Forma</th>
              <th className="px-4 py-2 font-semibold text-right">Valor</th>
              <th className="px-4 py-2 font-semibold">Assinatura</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(({ payment, tableNumber }) => (
              <tr key={payment.id} className="border-b border-border last:border-b-0">
                <td className="px-4 py-2.5 text-ink-soft font-data tabular-nums">
                  {formatDateTime(payment.created_at)}
                </td>
                <td className="px-4 py-2.5 text-ink-soft">{tableNumber ?? '—'}</td>
                <td className="px-4 py-2.5 text-ink-soft">
                  {payment.splits.map((s) => METHOD_LABELS[s.payment_method]).join(' + ')}
                  {payment.card_last4 && <span className="text-ink-soft/70"> •••• {payment.card_last4}</span>}
                </td>
                <td className="px-4 py-2.5 text-ink font-semibold font-data tabular-nums text-right">
                  R$ {payment.total_amount.toFixed(2)}
                </td>
                <td className="px-4 py-2.5">
                  {payment.signature_data ? (
                    <button
                      onClick={() => setViewingSignatureOf(payment)}
                      className="flex items-center gap-1 text-[11px] font-semibold text-ink-soft hover:text-ink"
                    >
                      <PenLine className="w-3.5 h-3.5" />
                      Ver
                    </button>
                  ) : (
                    <span className="text-ink-soft/50">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {viewingSignatureOf && (
        <SignatureModal payment={viewingSignatureOf} onClose={() => setViewingSignatureOf(null)} />
      )}
    </div>
  );
};
