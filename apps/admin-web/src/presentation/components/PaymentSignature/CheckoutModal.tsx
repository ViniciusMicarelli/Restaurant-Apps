import React, { useState } from 'react';
import { X } from 'lucide-react';
import type { Command } from '../../../infrastructure/api/diningApi';
import { useSessionStore } from '../../../infrastructure/state/sessionStore';
import { useMyOpenCashRegister, useOpenCashRegister, useProcessPayment } from '../../hooks/usePayments';
import { useCloseCommand } from '../../hooks/useCommands';
import { PaymentSignatureForm, type PaymentSignatureResult } from './PaymentSignatureForm';
import { PaymentMethodSelector, type CheckoutMethod } from './PaymentMethodSelector';
import { PixPaymentPanel } from './PixPaymentPanel';
import { CashPaymentPanel } from './CashPaymentPanel';
import { PaymentSuccessCelebration } from '../Rive/PaymentSuccessCelebration';

interface CheckoutModalProps {
  command: Command;
  /** Comanda pode ter mais de um pedido lançado — mantido como referência
   * secundária no `order_id` do pagamento (compatibilidade), mas quem
   * rastreia a comanda de verdade agora é `command.id` ("Payment por
   * Comanda", ver `useRevenue.ts`). */
  referenceOrderId: string;
  total: number;
  onClose: () => void;
  onPaid: () => void;
}

export const CheckoutModal: React.FC<CheckoutModalProps> = ({
  command,
  referenceOrderId,
  total,
  onClose,
  onPaid,
}) => {
  const currentUser = useSessionStore((state) => state.user);
  const cashRegisterQuery = useMyOpenCashRegister();
  const openCashRegister = useOpenCashRegister();
  const processPayment = useProcessPayment();
  const closeCommand = useCloseCommand();
  const [method, setMethod] = useState<CheckoutMethod>('CREDIT_CARD');
  const [showCelebration, setShowCelebration] = useState(false);
  // Uma chave por sessão do modal — reaproveitada em qualquer retry dentro
  // dela (evita duplicar o Payment numa reconexão de rede), nova se o
  // modal for fechado/reaberto.
  const [idempotencyKey] = useState(() => crypto.randomUUID());

  const cashRegister = cashRegisterQuery.data;
  const isSubmitting = processPayment.isPending || closeCommand.isPending;

  const handleOpenCashRegister = () => {
    if (!currentUser) return;
    openCashRegister.mutate({ operator_id: currentUser.id, opening_amount: 0 });
  };

  const submitPayment = (payload: {
    card_last4?: string;
    card_holder_name?: string;
    signature_data?: string;
  }) => {
    if (!cashRegister) return;
    processPayment.mutate(
      {
        payload: {
          order_id: referenceOrderId,
          command_id: command.id,
          cash_register_id: cashRegister.id,
          expected_total: total,
          splits: [{ payment_method: method, amount: total }],
          ...payload,
        },
        idempotencyKey,
      },
      {
        onSuccess: () => {
          closeCommand.mutate(command.id, { onSuccess: () => setShowCelebration(true) });
        },
      },
    );
  };

  const handleCardSubmit = (result: PaymentSignatureResult) =>
    submitPayment({
      card_last4: result.cardLast4,
      card_holder_name: result.cardHolderName,
      signature_data: result.signatureData,
    });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <header className="px-5 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white">
          <h3 className="text-sm font-bold text-gray-900">
            Fechar Comanda — {command.customer_name}
          </h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
            <X className="w-4 h-4" />
          </button>
        </header>

        <div className="p-5">
          {cashRegisterQuery.isLoading && (
            <p className="text-xs text-gray-500">Verificando caixa aberto...</p>
          )}
          {!cashRegisterQuery.isLoading && !cashRegister && (
            <div className="text-center">
              <p className="text-xs text-gray-600 mb-3">
                Você ainda não tem um caixa aberto — abra o seu pra poder receber o pagamento
                desta comanda.
              </p>
              <button
                onClick={handleOpenCashRegister}
                disabled={openCashRegister.isPending || !currentUser}
                className="w-full rounded-xl bg-gray-900 text-white text-sm font-semibold py-2.5 disabled:opacity-50"
              >
                {openCashRegister.isPending ? 'Abrindo caixa...' : 'Abrir meu caixa'}
              </button>
              {openCashRegister.isError && (
                <p className="text-xs text-red-600 mt-2">
                  Falha ao abrir o caixa: {(openCashRegister.error as Error).message}
                </p>
              )}
            </div>
          )}
          {cashRegister && (
            <>
              <PaymentMethodSelector value={method} onChange={setMethod} />

              {(method === 'CREDIT_CARD' || method === 'DEBIT_CARD') && (
                <PaymentSignatureForm
                  totalAmount={total}
                  isSubmitting={isSubmitting}
                  onSubmit={handleCardSubmit}
                  onCancel={onClose}
                />
              )}
              {method === 'PIX' && (
                <PixPaymentPanel
                  totalAmount={total}
                  isSubmitting={isSubmitting}
                  onConfirm={() => submitPayment({})}
                  onCancel={onClose}
                />
              )}
              {method === 'CASH' && (
                <CashPaymentPanel
                  totalAmount={total}
                  isSubmitting={isSubmitting}
                  onConfirm={() => submitPayment({})}
                  onCancel={onClose}
                />
              )}
            </>
          )}
          {processPayment.isError && (
            <p className="text-xs text-red-600 mt-3">
              Falha ao processar pagamento: {(processPayment.error as Error).message}
            </p>
          )}
        </div>
      </div>

      {showCelebration && (
        <PaymentSuccessCelebration
          message={`Comanda fechada!\nTotal: R$ ${total.toFixed(2)}`}
          onDone={onPaid}
        />
      )}
    </div>
  );
};
