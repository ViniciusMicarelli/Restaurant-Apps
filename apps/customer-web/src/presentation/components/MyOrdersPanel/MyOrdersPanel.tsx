import React, { useEffect, useRef, useState } from 'react';
import { X, Clock, ReceiptText } from 'lucide-react';
import { useMyOrders } from '../../hooks/useMyOrders';
import type { OrderStatus } from '../../../infrastructure/api/orderApi';
import { OrderReadyCelebration } from '../Rive/OrderReadyCelebration';
import { CustomerCheckoutModal } from '../CustomerCheckout/CustomerCheckoutModal';

const STATUS_LABEL: Record<OrderStatus, string> = {
  PENDING: 'Recebido',
  PREPARING: 'Em preparo',
  READY: 'Pronto',
  DELIVERED: 'Entregue',
  CANCELLED: 'Cancelado',
};

const STATUS_STYLE: Record<OrderStatus, string> = {
  PENDING: 'bg-gray-100 text-gray-600',
  PREPARING: 'bg-amber-100 text-amber-700',
  READY: 'bg-emerald-100 text-emerald-700',
  DELIVERED: 'bg-blue-100 text-blue-700',
  CANCELLED: 'bg-red-100 text-red-700',
};

interface MyOrdersPanelProps {
  tenantId: string | undefined;
  tableNumber: number | null;
  /** Secret de QR Code da mesa — necessária pro botão "Fechar minha conta"
   * (US-05.4). Sem ela (raro: painel aberto sem sessão de mesa válida), o
   * botão não aparece. */
  secret: string | null;
  serviceFeePercent: number;
  onClose: () => void;
}

/**
 * "O que foi pedido e solicitado" — visão dos pedidos da mesa com status ao
 * vivo (polling 5s), mais o botão "Fechar minha conta" (US-05.4): o cliente
 * pode pagar e encerrar a própria comanda pelo celular, sem esperar o
 * garçom com a maquininha — canal complementar, não substituto (quem chegar
 * primeiro fecha a comanda).
 */
export const MyOrdersPanel: React.FC<MyOrdersPanelProps> = ({
  tenantId,
  tableNumber,
  secret,
  serviceFeePercent,
  onClose,
}) => {
  const [showCheckout, setShowCheckout] = useState(false);
  const [paidAndClosed, setPaidAndClosed] = useState(false);

  const ordersQuery = useMyOrders(tenantId, tableNumber, !paidAndClosed);
  const orders = ordersQuery.data ?? [];

  // Celebra a primeira vez que um pedido desta mesa vira READY — guarda o
  // último status visto por pedido pra não repetir a cada poll (5s).
  const lastSeenStatus = useRef<Record<string, OrderStatus>>({});
  const [readyCelebration, setReadyCelebration] = useState<string | null>(null);

  useEffect(() => {
    for (const order of orders) {
      const previous = lastSeenStatus.current[order.id];
      if (order.status === 'READY' && previous && previous !== 'READY') {
        setReadyCelebration(order.id);
      }
      lastSeenStatus.current[order.id] = order.status;
    }
  }, [orders]);

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />
      <aside className="fixed right-0 top-0 h-full w-full max-w-sm bg-white shadow-2xl z-50 flex flex-col">
        <header className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-900">Meu Pedido — Mesa {tableNumber}</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
            <X className="w-4 h-4" />
          </button>
        </header>

        {paidAndClosed ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-2 p-6 text-center">
            <ReceiptText className="w-10 h-10 text-emerald-500" />
            <p className="text-sm font-semibold text-gray-900">Obrigado pela visita!</p>
            <p className="text-xs text-gray-500">Sua conta foi paga e a mesa foi encerrada.</p>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {ordersQuery.isLoading && <p className="text-xs text-gray-500">Carregando...</p>}
              {orders.length === 0 && !ordersQuery.isLoading && (
                <p className="text-xs text-gray-500">Nenhum pedido lançado para esta mesa ainda.</p>
              )}
              {orders.map((order) => (
                <div key={order.id} className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1 ${STATUS_STYLE[order.status]}`}>
                      <Clock className="w-3 h-3" />
                      {STATUS_LABEL[order.status]}
                    </span>
                    <span className="text-xs font-bold text-gray-900">R$ {order.total_amount.toFixed(2)}</span>
                  </div>
                  {order.items.map((item, index) => (
                    <p key={index} className="text-xs text-gray-600">
                      {item.quantity}x {item.product_name}
                    </p>
                  ))}
                </div>
              ))}
            </div>

            {secret && orders.length > 0 && (
              <div className="p-5 border-t border-gray-100">
                <button
                  onClick={() => setShowCheckout(true)}
                  className="w-full rounded-xl bg-gray-900 text-white text-sm font-semibold py-2.5"
                >
                  Fechar minha conta
                </button>
              </div>
            )}
          </>
        )}
      </aside>

      {readyCelebration && (
        <OrderReadyCelebration
          message="Seu pedido está pronto!"
          onDone={() => setReadyCelebration(null)}
        />
      )}

      {showCheckout && tenantId && tableNumber && secret && (
        <CustomerCheckoutModal
          tenantId={tenantId}
          tableNumber={tableNumber}
          secret={secret}
          orders={orders}
          serviceFeePercent={serviceFeePercent}
          onClose={() => setShowCheckout(false)}
          onPaid={() => {
            setShowCheckout(false);
            setPaidAndClosed(true);
          }}
        />
      )}
    </>
  );
};
