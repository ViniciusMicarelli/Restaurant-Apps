import React, { useState, useEffect } from 'react';
import { Sidebar, type AdminTab } from '../components/Sidebar/Sidebar';
import { ElapsedTime, getElapsedUrgency } from '../components/ElapsedTime/ElapsedTime';
import { NotificationBell } from '../components/NotificationBell/NotificationBell';
import { CommandDrawer } from '../components/CommandDrawer/CommandDrawer';
import { CheckoutModal } from '../components/PaymentSignature/CheckoutModal';
import { TableQrModal } from '../components/TableQrModal/TableQrModal';
import { StatusPill, statusStripeClassName, type StatusTone } from '../components/StatusBadge/StatusBadge';
import { DollarSign, CheckCircle2, Users, Clock, Plus, Wallet, QrCode, SprayCan } from 'lucide-react';
import { useRestaurant, useUpdateBranding } from '../hooks/useRestaurant';
import { useTables, useCreateTable, useMarkTableCleaned } from '../hooks/useTables';
import { useRevenue } from '../hooks/useRevenue';
import { useDashboardMetrics } from '../hooks/useDashboardMetrics';
import { OwnerDashboardOverview } from '../components/Dashboard/OwnerDashboardOverview';
import { StatTile } from '../components/Dashboard/StatTile';
import { PaymentHistoryTable } from '../components/Revenue/PaymentHistoryTable';
import { useSessionStore } from '../../infrastructure/state/sessionStore';
import { useKdsItems, useUpdateKdsItemStatus } from '../hooks/useKdsItems';
import type { UpdateBrandingRequest } from '../../infrastructure/api/restaurantApi';
import type { KdsItemStatus } from '../../infrastructure/api/kitchenApi';
import type { Table, Command } from '../../infrastructure/api/diningApi';

const MANAGEMENT_ROLES = new Set(['RESTAURANT_OWNER', 'MANAGER']);

// `OCCUPIED` usa o acento de marca, não vermelho de alerta — mesa ocupada
// é o uso normal da mesa, não um problema (direção visual, 2026-08-10,
// docs/logs/2026-08-10.md Sessão 8). `critical` fica reservado só pra
// estados que realmente pedem atenção urgente (ex: ticket de KDS atrasado).
const TABLE_STATUS_TONE: Record<string, StatusTone> = {
  AVAILABLE: 'good',
  OCCUPIED: 'accent',
  RESERVED: 'info',
  WAITING_CLEANING: 'warning',
};

const TABLE_STATUS_LABEL: Record<string, string> = {
  AVAILABLE: 'Livre',
  OCCUPIED: 'Ocupada',
  RESERVED: 'Reservada',
  WAITING_CLEANING: 'Aguardando Limpeza',
};

const NEXT_KDS_STATUS: Partial<Record<KdsItemStatus, KdsItemStatus>> = {
  PENDING: 'PREPARING',
  PREPARING: 'READY',
  READY: 'DELIVERED',
};

const KDS_STATUS_LABEL: Record<KdsItemStatus, string> = {
  PENDING: 'Pendente',
  PREPARING: 'Preparando',
  READY: 'Pronto',
  DELIVERED: 'Entregue',
};

const KDS_STATUS_TONE: Record<KdsItemStatus, StatusTone> = {
  PENDING: 'warning',
  PREPARING: 'info',
  READY: 'good',
  DELIVERED: 'good',
};

// Só PENDING/PREPARING escalam pra "Atrasado" — READY já saiu da fila de
// preparo (é a cozinha esperando o garçom retirar, não mais um problema
// de SLA de cozinha) e DELIVERED já terminou.
const OVERDUE_ELIGIBLE_STATUSES: ReadonlySet<KdsItemStatus> = new Set(['PENDING', 'PREPARING']);

export const AdminDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AdminTab>('dashboard');

  const restaurantQuery = useRestaurant();
  const tablesQuery = useTables();
  const kdsQuery = useKdsItems();
  const updateBranding = useUpdateBranding();
  const updateKdsStatus = useUpdateKdsItemStatus();
  const createTable = useCreateTable();
  const markTableCleaned = useMarkTableCleaned();
  const revenueQuery = useRevenue();
  const role = useSessionStore((state) => state.user?.role);
  const canManageTables = Boolean(role && MANAGEMENT_ROLES.has(role));
  const dashboardMetricsQuery = useDashboardMetrics({ enabled: canManageTables });

  const [brandingForm, setBrandingForm] = useState<UpdateBrandingRequest | null>(null);
  const [showCreateTableForm, setShowCreateTableForm] = useState(false);
  const [newTableNumber, setNewTableNumber] = useState('');
  const [newTableCapacity, setNewTableCapacity] = useState('');
  const [selectedTable, setSelectedTable] = useState<Table | null>(null);
  const [qrTable, setQrTable] = useState<Table | null>(null);
  const [checkout, setCheckout] = useState<{ command: Command; referenceOrderId: string; total: number } | null>(
    null,
  );

  useEffect(() => {
    if (restaurantQuery.data && !brandingForm) {
      const { css_variables: _cssVariables, ...editable } = restaurantQuery.data.branding;
      setBrandingForm(editable);
    }
  }, [restaurantQuery.data, brandingForm]);

  const handleCreateTable = (event: React.FormEvent) => {
    event.preventDefault();
    const number = Number(newTableNumber);
    const capacity = Number(newTableCapacity);
    if (!number || !capacity) return;
    createTable.mutate(
      { number, capacity },
      {
        onSuccess: () => {
          setNewTableNumber('');
          setNewTableCapacity('');
          setShowCreateTableForm(false);
        },
      },
    );
  };

  const occupiedTables = tablesQuery.data?.filter((t) => t.status === 'OCCUPIED').length ?? 0;
  const totalTables = tablesQuery.data?.length ?? 0;
  const pendingKdsItems = kdsQuery.data?.filter((i) => i.status !== 'DELIVERED').length ?? 0;

  return (
    <div className="min-h-screen flex bg-gray-100 font-sans">
      <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />

      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              {activeTab === 'dashboard' &&
                (canManageTables ? 'Dashboard Completo' : 'Painel de Controle Operacional')}
              {activeTab === 'tables' && 'Mapa de Mesas & Comandas do Salão'}
              {activeTab === 'kds' && 'Kitchen Display System (KDS Cozinha)'}
              {activeTab === 'revenue' && 'Faturamento'}
              {activeTab === 'branding' && 'Personalização do Tema White-Label'}
            </h2>
            <p className="text-xs text-gray-500">
              {restaurantQuery.data?.trade_name ?? 'Carregando restaurante...'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <NotificationBell />
          </div>
        </header>

        <div className="p-6">
          {activeTab === 'dashboard' && canManageTables && (
            <OwnerDashboardOverview
              metrics={dashboardMetricsQuery.data}
              isLoading={dashboardMetricsQuery.isLoading}
              occupiedTables={occupiedTables}
              totalTables={totalTables}
              pendingKdsItems={pendingKdsItems}
            />
          )}

          {activeTab === 'dashboard' && !canManageTables && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between text-gray-500 mb-2">
                  <span className="text-xs font-semibold">Taxa de Serviço</span>
                  <DollarSign className="w-4 h-4 text-emerald-500" />
                </div>
                <p className="text-xl font-extrabold text-gray-900">
                  {restaurantQuery.data ? `${restaurantQuery.data.service_fee_percent}%` : '—'}
                </p>
              </div>

              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between text-gray-500 mb-2">
                  <span className="text-xs font-semibold">Itens Pendentes no KDS</span>
                  <CheckCircle2 className="w-4 h-4 text-blue-500" />
                </div>
                <p className="text-xl font-extrabold text-gray-900">{pendingKdsItems} itens</p>
              </div>

              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between text-gray-500 mb-2">
                  <span className="text-xs font-semibold">Mesas Ocupadas</span>
                  <Users className="w-4 h-4 text-amber-500" />
                </div>
                <p className="text-xl font-extrabold text-gray-900">
                  {occupiedTables} / {totalTables} mesas
                </p>
              </div>

              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between text-gray-500 mb-2">
                  <span className="text-xs font-semibold">Moeda</span>
                  <Clock className="w-4 h-4 text-purple-500" />
                </div>
                <p className="text-xl font-extrabold text-gray-900">{restaurantQuery.data?.currency ?? '—'}</p>
              </div>
            </div>
          )}

          {activeTab === 'tables' && (
            <div>
              {canManageTables && (
                <div className="mb-4">
                  {!showCreateTableForm ? (
                    <button
                      onClick={() => setShowCreateTableForm(true)}
                      className="flex items-center gap-1.5 text-xs font-bold bg-red-600 text-white px-3 py-2 rounded-xl shadow-md"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Nova Mesa
                    </button>
                  ) : (
                    <form
                      onSubmit={handleCreateTable}
                      className="bg-white rounded-2xl p-4 border border-gray-200 shadow-sm flex items-end gap-3 max-w-md"
                    >
                      <div>
                        <label className="text-xs font-semibold text-gray-700 block mb-1">Número</label>
                        <input
                          type="number"
                          min={1}
                          required
                          value={newTableNumber}
                          onChange={(e) => setNewTableNumber(e.target.value)}
                          className="w-24 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-gray-700 block mb-1">Lugares</label>
                        <input
                          type="number"
                          min={1}
                          required
                          value={newTableCapacity}
                          onChange={(e) => setNewTableCapacity(e.target.value)}
                          className="w-24 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={createTable.isPending}
                        className="bg-red-600 disabled:bg-red-300 text-white font-bold text-xs px-4 py-2 rounded-xl shadow-md"
                      >
                        {createTable.isPending ? 'Salvando...' : 'Salvar'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowCreateTableForm(false)}
                        className="text-xs font-semibold text-gray-500 px-2 py-2"
                      >
                        Cancelar
                      </button>
                    </form>
                  )}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                {tablesQuery.isLoading && <p className="text-sm text-gray-500">Carregando mesas...</p>}
                {tablesQuery.data?.map((table) => {
                  const tone = TABLE_STATUS_TONE[table.status] ?? 'info';
                  return (
                    <div
                      key={table.id}
                      onClick={() => table.status === 'OCCUPIED' && setSelectedTable(table)}
                      className={`text-left rounded-xl p-5 bg-surface border border-border shadow-sm ${statusStripeClassName(
                        tone,
                      )} ${table.status === 'OCCUPIED' ? 'cursor-pointer hover:brightness-95' : ''}`}
                    >
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-lg font-bold font-display text-ink">Mesa {table.number}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setQrTable(table);
                          }}
                          title="Ver QR Code"
                          className="p-1 rounded-md bg-paper hover:bg-border/50"
                        >
                          <QrCode className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <StatusPill tone={tone} label={TABLE_STATUS_LABEL[table.status]} />
                      <p className="text-[10px] font-semibold mt-2 text-ink-soft">
                        {table.capacity} lugares{table.status === 'OCCUPIED' ? ' • Ver comanda →' : ''}
                      </p>
                      {table.status === 'WAITING_CLEANING' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            markTableCleaned.mutate(table.id);
                          }}
                          disabled={markTableCleaned.isPending}
                          className="mt-3 w-full flex items-center justify-center gap-1.5 text-[11px] font-bold bg-warning-soft hover:brightness-95 text-warning px-2 py-1.5 rounded-lg disabled:opacity-50"
                        >
                          <SprayCan className="w-3.5 h-3.5" />
                          Mesa Limpa
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === 'kds' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {kdsQuery.isLoading && <p className="text-sm text-gray-500">Carregando itens do KDS...</p>}
              {kdsQuery.data?.length === 0 && (
                <p className="text-sm text-gray-500">Nenhum item na esteira no momento.</p>
              )}
              {kdsQuery.data?.map((item) => {
                const isOverdue =
                  OVERDUE_ELIGIBLE_STATUSES.has(item.status) &&
                  getElapsedUrgency(Date.now() - new Date(item.created_at).getTime()) === 'critical';
                const tone: StatusTone = isOverdue ? 'critical' : KDS_STATUS_TONE[item.status];
                const label = isOverdue ? 'Atrasado' : KDS_STATUS_LABEL[item.status];
                return (
                  <div
                    key={item.id}
                    className={`bg-surface rounded-xl p-4 border border-border shadow-sm ${statusStripeClassName(tone)}`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-bold text-ink">{item.product_name}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-paper text-ink-soft">
                        {item.station}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-xs text-ink-soft">
                        Qtd: {item.quantity}
                        {item.table_number ? ` • Mesa ${item.table_number}` : ''}
                      </p>
                      <ElapsedTime createdAt={item.created_at} />
                    </div>
                    <div className="flex items-center justify-between">
                      <StatusPill tone={tone} label={label} />
                      {NEXT_KDS_STATUS[item.status] && (
                        <button
                          onClick={() =>
                            updateKdsStatus.mutate({ itemId: item.id, newStatus: NEXT_KDS_STATUS[item.status]! })
                          }
                          disabled={updateKdsStatus.isPending}
                          className="text-xs font-bold bg-accent disabled:opacity-50 text-accent-ink px-3 py-1.5 rounded-lg hover:brightness-95"
                        >
                          Avançar para {KDS_STATUS_LABEL[NEXT_KDS_STATUS[item.status]!]}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === 'revenue' && (
            <div>
              {revenueQuery.isLoading && <p className="text-sm text-gray-500">Calculando faturamento...</p>}
              {revenueQuery.data && (
                <>
                  {(() => {
                    const feePercent = restaurantQuery.data?.service_fee_percent ?? 0;
                    const serviceFeeTotal = revenueQuery.data.closedCommandsWithFee.reduce(
                      (sum, { ordersTotal }) => sum + ordersTotal * (feePercent / 100),
                      0,
                    );
                    return (
                      <>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                          <StatTile
                            label="Faturamento Total"
                            value={`R$ ${revenueQuery.data.totalRevenue.toFixed(2)}`}
                            hint={`${revenueQuery.data.paymentsCount} pagamento(s) aprovado(s)`}
                            icon={Wallet}
                            tone="good"
                          />
                          <StatTile
                            label={`Taxa de Serviço (${feePercent}%)`}
                            value={`R$ ${serviceFeeTotal.toFixed(2)}`}
                            hint={`${revenueQuery.data.closedCommandsWithFee.length} comanda(s) com taxa cobrada`}
                            icon={DollarSign}
                          />
                          <StatTile
                            label="Comandas Fechadas"
                            value={String(revenueQuery.data.closedCommandsCount)}
                            icon={CheckCircle2}
                          />
                        </div>

                        <div className="bg-surface rounded-xl border border-border shadow-sm overflow-hidden">
                          <div className="px-4 py-3 border-b border-border">
                            <span className="text-xs font-bold font-display text-ink">
                              Comandas fechadas com taxa de serviço
                            </span>
                          </div>
                          {revenueQuery.data.closedCommandsWithFee.length === 0 && (
                            <p className="text-xs text-ink-soft px-4 py-3">
                              Nenhuma comanda fechada com taxa de serviço cobrada ainda.
                            </p>
                          )}
                          {revenueQuery.data.closedCommandsWithFee.map(({ command, ordersTotal }) => (
                            <div
                              key={command.id}
                              className="px-4 py-3 border-b border-border last:border-b-0 flex items-center justify-between"
                            >
                              <span className="text-xs text-ink-soft">{command.customer_name}</span>
                              <span className="text-xs font-semibold font-data tabular-nums text-ink">
                                Pedidos: R$ {ordersTotal.toFixed(2)} • Taxa: R${' '}
                                {(ordersTotal * (feePercent / 100)).toFixed(2)}
                              </span>
                            </div>
                          ))}
                        </div>

                        <div className="mt-6">
                          <PaymentHistoryTable entries={revenueQuery.data.paymentHistory} />
                        </div>
                      </>
                    );
                  })()}
                </>
              )}
            </div>
          )}

          {activeTab === 'branding' && brandingForm && (
            <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm max-w-xl">
              <h3 className="text-sm font-bold text-gray-900 mb-4">
                Configuração de Tema White-Label para Apps e Web
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-gray-700 block mb-1">
                    Cor Primária Oficial (HEX)
                  </label>
                  <input
                    type="text"
                    value={brandingForm.primary_color}
                    onChange={(e) => setBrandingForm({ ...brandingForm, primary_color: e.target.value })}
                    className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-700 block mb-1">URL da Logomarca</label>
                  <input
                    type="text"
                    value={brandingForm.logo_url}
                    onChange={(e) => setBrandingForm({ ...brandingForm, logo_url: e.target.value })}
                    className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs"
                  />
                </div>

                <button
                  onClick={() => updateBranding.mutate(brandingForm)}
                  disabled={updateBranding.isPending}
                  className="bg-red-600 disabled:bg-red-300 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-md"
                >
                  {updateBranding.isPending ? 'Salvando...' : 'Salvar no Banco de Dados (SaaS Tenant)'}
                </button>
                {updateBranding.isSuccess && (
                  <span className="ml-3 text-xs font-semibold text-emerald-600">Salvo com sucesso!</span>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {selectedTable && (
        <CommandDrawer
          table={selectedTable}
          onClose={() => setSelectedTable(null)}
          onCheckout={({ command, referenceOrderId, total }) => {
            setSelectedTable(null);
            setCheckout({ command, referenceOrderId, total });
          }}
        />
      )}

      {checkout && (
        <CheckoutModal
          command={checkout.command}
          referenceOrderId={checkout.referenceOrderId}
          total={checkout.total}
          onClose={() => setCheckout(null)}
          onPaid={() => setCheckout(null)}
        />
      )}

      {qrTable && restaurantQuery.data && (
        <TableQrModal
          table={qrTable}
          restaurantSlug={restaurantQuery.data.slug}
          onClose={() => setQrTable(null)}
        />
      )}
    </div>
  );
};
