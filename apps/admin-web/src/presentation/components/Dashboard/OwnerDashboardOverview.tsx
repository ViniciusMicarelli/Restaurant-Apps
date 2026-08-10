import React from 'react';
import {
  ShoppingBag,
  CalendarDays,
  Receipt,
  Users,
  Clock,
  Timer,
  CheckCircle2,
  UtensilsCrossed,
} from 'lucide-react';
import { StatTile } from './StatTile';
import { MonthlyBarChart } from './MonthlyBarChart';
import { TopProductsChart } from './TopProductsChart';
import { RiveLoadingIndicator } from '../Rive/RiveLoadingIndicator';
import type { DashboardMetrics } from '../../hooks/useDashboardMetrics';

// Paleta categórica validada (skill de dataviz, palette.md) — ordem fixa,
// um hue por contexto de magnitude simultâneo no dashboard.
const COLOR_ORDERS = '#2a78d6'; // slot 1 azul
const COLOR_REVENUE = '#eb6834'; // slot 2 laranja
const COLOR_PRODUCTS = '#1baf7a'; // slot 3 aqua

interface OwnerDashboardOverviewProps {
  metrics: DashboardMetrics | undefined;
  isLoading: boolean;
  occupiedTables: number;
  totalTables: number;
  pendingKdsItems: number;
}

function formatCurrencyCompact(value: number): string {
  if (value >= 1000) return `R$ ${(value / 1000).toFixed(1)}k`;
  return `R$ ${value.toFixed(0)}`;
}

function formatMinutes(minutes: number | null): string {
  if (minutes === null) return '—';
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60);
    const rest = Math.round(minutes % 60);
    return `${hours}h ${rest}min`;
  }
  return `${Math.round(minutes)}min`;
}

function slaTone(compliancePct: number | null): 'default' | 'good' | 'warning' | 'critical' {
  if (compliancePct === null) return 'default';
  if (compliancePct >= 90) return 'good';
  if (compliancePct >= 70) return 'warning';
  return 'critical';
}

/**
 * Dashboard completo do dono/gerente — pedidos, mesas, tempo por mesa e SLA
 * da cozinha (docs/logs/2026-08-06.md). Papéis operacionais (garçom, caixa,
 * cozinha) continuam vendo só o resumo enxuto anterior, na própria
 * `AdminDashboardPage` — este componente é OWNER/MANAGER only.
 */
export const OwnerDashboardOverview: React.FC<OwnerDashboardOverviewProps> = ({
  metrics,
  isLoading,
  occupiedTables,
  totalTables,
  pendingKdsItems,
}) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatTile label="Mesas Ocupadas" value={`${occupiedTables} / ${totalTables}`} icon={Users} />
        <StatTile label="Itens Pendentes no KDS" value={`${pendingKdsItems} itens`} icon={CheckCircle2} />
        <StatTile
          label="Pedidos Hoje"
          value={isLoading ? '—' : String(metrics?.ordersToday ?? 0)}
          icon={ShoppingBag}
        />
        <StatTile
          label="Pedidos no Mês"
          value={isLoading ? '—' : String(metrics?.ordersThisMonth ?? 0)}
          icon={CalendarDays}
        />
        <StatTile
          label="Ticket Médio"
          value={isLoading ? '—' : `R$ ${(metrics?.averageTicket ?? 0).toFixed(2)}`}
          icon={Receipt}
        />
        <StatTile
          label="Mesas Atendidas Hoje"
          value={isLoading ? '—' : String(metrics?.tablesServedToday ?? 0)}
          hint={metrics ? `${metrics.openTablesRightNow} aberta(s) agora` : undefined}
          icon={UtensilsCrossed}
        />
        <StatTile
          label="Tempo Médio por Mesa"
          value={isLoading ? '—' : formatMinutes(metrics?.avgTableTimeMinutes ?? null)}
          hint={metrics ? `${metrics.closedCommandsSample} comanda(s) fechada(s)` : undefined}
          icon={Clock}
        />
        <StatTile
          label="SLA da Cozinha (Hoje)"
          value={isLoading || !metrics?.kitchenSampleToday ? '—' : `${Math.round(metrics.kitchenSlaComplianceTodayPct ?? 0)}%`}
          hint={
            metrics?.kitchenSampleToday
              ? `Média ${formatMinutes(metrics.kitchenAvgPrepMinutesToday)} • meta ≤${metrics.kitchenSlaTargetMinutes}min • ${metrics.kitchenSampleToday} item(ns)`
              : 'Sem itens prontos hoje ainda'
          }
          icon={Timer}
          tone={slaTone(metrics?.kitchenSampleToday ? metrics.kitchenSlaComplianceTodayPct : null)}
        />
      </div>

      {!isLoading && metrics && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <MonthlyBarChart
              title="Pedidos por Mês (últimos 6 meses)"
              data={metrics.monthlyTrend.map((m) => ({ label: m.label, value: m.orderCount }))}
              color={COLOR_ORDERS}
            />
            <MonthlyBarChart
              title="Valor em Pedidos por Mês (bruto, não é o Faturamento pago)"
              data={metrics.monthlyTrend.map((m) => ({ label: m.label, value: m.revenue }))}
              color={COLOR_REVENUE}
              valueFormatter={formatCurrencyCompact}
            />
          </div>

          <TopProductsChart products={metrics.topProducts} color={COLOR_PRODUCTS} />
        </>
      )}

      {isLoading && (
        <div className="flex flex-col items-center gap-2 py-6">
          <RiveLoadingIndicator size={72} />
          <p className="text-xs text-gray-500">Calculando métricas do dashboard...</p>
        </div>
      )}
    </div>
  );
};
