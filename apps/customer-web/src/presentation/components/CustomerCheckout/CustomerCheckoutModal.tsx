import React, { useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import type { OrderDto } from '../../../infrastructure/api/orderApi';
import { useOpenCommand, useSubmitCustomerCheckout } from '../../hooks/useCommandCheckout';
import { RiveLoadingIndicator } from '../Rive/RiveLoadingIndicator';
import { OrderReadyCelebration } from '../Rive/OrderReadyCelebration';
import { CustomerCardForm } from './CustomerCardForm';
import { CustomerPixPanel } from './CustomerPixPanel';
import { PaymentMethodSelector, type CustomerCheckoutMethod } from './PaymentMethodSelector';

interface CustomerCheckoutModalProps {
  tenantId: string;
  tableNumber: number;
  secret: string;
  orders: OrderDto[];
  serviceFeePercent: number;
  onClose: () => void;
  /** Chamado depois que o pagamento foi aprovado (e a comanda, fechada). */
  onPaid: () => void;
}

/**
 * "Fechar minha conta" — checkout de autoatendimento do cliente (US-05.4),
 * complementar ao fluxo do garçom com a maquininha no `admin-web` (não o
 * substitui: quem chegar primeiro fecha a comanda). Sem assinatura — essa
 * etapa do fluxo do garçom existe como evidência de conferência presencial,
 * e não se aplica a um pagamento que o cliente faz sozinho no próprio
 * celular. Sem Dinheiro como opção — não faz sentido remoto.
 */
export const CustomerCheckoutModal: React.FC<CustomerCheckoutModalProps> = ({
  tenantId,
  tableNumber,
  secret,
  orders,
  serviceFeePercent,
  onClose,
  onPaid,
}) => {
  const [method, setMethod] = useState<CustomerCheckoutMethod>('CREDIT_CARD');
  const [showCelebration, setShowCelebration] = useState(false);
  // Uma chave por sessão do modal — reaproveitada em qualquer retry dentro
  // dela (evita duplicar o Payment numa reconexão de rede), nova se o
  // modal for fechado/reaberto.
  const [idempotencyKey] = useState(() => crypto.randomUUID());

  const openCommandQuery = useOpenCommand(tenantId, tableNumber, secret, true);
  const checkout = useSubmitCustomerCheckout(tenantId, secret);

  // Só pra exibir o valor e dimensionar o `amount` da parcela enviada — a
  // fonte de verdade que decide se o pagamento é aprovado é o total
  // recalculado no servidor (ver paymentApi.ts). Exclui pedidos CANCELLED
  // pra bater com o cálculo do servidor (nunca cobra por um pedido
  // cancelado — divergir aqui só geraria um 422 à toa no happy path).
  const ordersTotal = orders
    .filter((order) => order.status !== 'CANCELLED')
    .reduce((sum, order) => sum + order.total_amount, 0);
  const command = openCommandQuery.data;
  const total = command?.service_fee_charged
    ? Math.round(ordersTotal * (1 + serviceFeePercent / 100) * 100) / 100
    : ordersTotal;

  const submit = (payload: { card_last4?: string; card_holder_name?: string }) => {
    if (!command || orders.length === 0) return;
    checkout.mutate(
      {
        commandId: command.id,
        idempotencyKey,
        payload: {
          table_number: tableNumber,
          secret,
          splits: [{ payment_method: method, amount: total }],
          ...payload,
        },
      },
      { onSuccess: () => setShowCelebration(true) },
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <header className="px-5 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white">
          <h3 className="text-sm font-bold text-gray-900">Fechar minha conta</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
            <X className="w-4 h-4" />
          </button>
        </header>

        <div className="p-5">
          {openCommandQuery.isLoading && (
            <div className="flex flex-col items-center gap-2 py-6">
              <RiveLoadingIndicator size={64} />
              <p className="text-xs text-gray-500">Carregando sua comanda...</p>
            </div>
          )}

          {openCommandQuery.isError && (
            <div className="text-center py-4">
              <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-gray-800">
                Não encontramos uma comanda aberta pra esta mesa
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Ela pode já ter sido fechada — peça ajuda a um garçom se não for o caso.
              </p>
            </div>
          )}

          {command && (
            <>
              <PaymentMethodSelector value={method} onChange={setMethod} />

              {(method === 'CREDIT_CARD' || method === 'DEBIT_CARD') && (
                <CustomerCardForm
                  totalAmount={total}
                  isSubmitting={checkout.isPending}
                  onSubmit={(result) =>
                    submit({ card_last4: result.cardLast4, card_holder_name: result.cardHolderName })
                  }
                  onCancel={onClose}
                />
              )}
              {method === 'PIX' && (
                <CustomerPixPanel
                  totalAmount={total}
                  isSubmitting={checkout.isPending}
                  onConfirm={() => submit({})}
                  onCancel={onClose}
                />
              )}
            </>
          )}

          {checkout.isError && (
            <p className="text-xs text-red-600 mt-3">
              Falha ao processar o pagamento: {(checkout.error as Error).message}
            </p>
          )}
        </div>
      </div>

      {showCelebration && (
        <OrderReadyCelebration
          message={`Obrigado! Sua conta foi paga.\nTotal: R$ ${total.toFixed(2)}`}
          onDone={onPaid}
        />
      )}
    </div>
  );
};
