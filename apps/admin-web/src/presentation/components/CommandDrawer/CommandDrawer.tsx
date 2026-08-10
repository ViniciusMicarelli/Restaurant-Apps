import React from 'react';
import { X, Receipt } from 'lucide-react';
import type { Table, Command } from '../../../infrastructure/api/diningApi';
import { useCommands, useSetCommandServiceFee } from '../../hooks/useCommands';
import { useOrdersByCommand } from '../../hooks/useOrders';

interface CommandDrawerProps {
  table: Table;
  onClose: () => void;
  /** Acionado ao clicar "Fechar e Cobrar" — quem abre o fluxo de pagamento é o pai. */
  onCheckout: (params: { command: Command; referenceOrderId: string; total: number }) => void;
}

/**
 * Painel lateral com o detalhe da comanda aberta numa mesa: pedidos
 * lançados, total corrente e o toggle "taxa de serviço cobrada" (fica a
 * cargo do garçom marcar — docs/modules/module_breakdown.md §8).
 */
export const CommandDrawer: React.FC<CommandDrawerProps> = ({ table, onClose, onCheckout }) => {
  const openCommandsQuery = useCommands('OPEN');
  const command = openCommandsQuery.data?.find((c) => c.table_id === table.id);
  const ordersQuery = useOrdersByCommand(command?.id);
  const setServiceFee = useSetCommandServiceFee();

  const orders = ordersQuery.data ?? [];
  const total = orders.reduce((sum, order) => sum + order.total_amount, 0);

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-30" onClick={onClose} />
      <aside className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-2xl z-40 flex flex-col">
        <header className="px-5 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-gray-900">Comanda — Mesa {table.number}</h3>
            {command && <p className="text-xs text-gray-500">{command.customer_name}</p>}
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
            <X className="w-4 h-4" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-5">
          {openCommandsQuery.isLoading && <p className="text-xs text-gray-500">Carregando comanda...</p>}
          {!openCommandsQuery.isLoading && !command && (
            <p className="text-xs text-gray-500">Nenhuma comanda aberta nesta mesa no momento.</p>
          )}

          {command && (
            <>
              <div className="space-y-3 mb-6">
                {ordersQuery.isLoading && <p className="text-xs text-gray-500">Carregando pedidos...</p>}
                {orders.length === 0 && !ordersQuery.isLoading && (
                  <p className="text-xs text-gray-500">Nenhum pedido lançado ainda.</p>
                )}
                {orders.map((order) => (
                  <div key={order.id} className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-gray-200 text-gray-700">
                        {order.status}
                      </span>
                      <span className="text-xs font-bold text-gray-900">
                        R$ {order.total_amount.toFixed(2)}
                      </span>
                    </div>
                    {order.items.map((item, index) => (
                      <p key={index} className="text-xs text-gray-600">
                        {item.quantity}x {item.product_name}
                      </p>
                    ))}
                  </div>
                ))}
              </div>

              <label className="flex items-center gap-2 mb-6 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={command.service_fee_charged}
                  disabled={setServiceFee.isPending}
                  onChange={(e) =>
                    setServiceFee.mutate({ commandId: command.id, charged: e.target.checked })
                  }
                  className="w-4 h-4 accent-red-600"
                />
                <span className="text-xs font-semibold text-gray-700">Taxa de serviço cobrada</span>
              </label>
            </>
          )}
        </div>

        {command && (
          <footer className="p-5 border-t border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-gray-500">Total da comanda</span>
              <span className="text-lg font-extrabold text-gray-900">R$ {total.toFixed(2)}</span>
            </div>
            <button
              onClick={() => onCheckout({ command, referenceOrderId: orders[0].id, total })}
              disabled={orders.length === 0}
              className="w-full flex items-center justify-center gap-2 bg-red-600 disabled:bg-red-300 text-white font-bold text-sm px-5 py-2.5 rounded-xl shadow-md"
            >
              <Receipt className="w-4 h-4" />
              Fechar e Cobrar
            </button>
          </footer>
        )}
      </aside>
    </>
  );
};
