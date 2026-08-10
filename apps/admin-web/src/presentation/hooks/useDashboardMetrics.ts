import { useQuery } from '@tanstack/react-query';
import { listOrders, type Order } from '../../infrastructure/api/orderApi';
import { listCommands, type Command } from '../../infrastructure/api/diningApi';
import { listKdsItems, type KdsItem } from '../../infrastructure/api/kitchenApi';

const DASHBOARD_POLL_INTERVAL_MS = 30_000;
const MONTHS_IN_TREND = 6;

/** Meta de tempo de preparo da cozinha (pedido entra na esteira -> fica
 * pronto) usada para calcular o % de aderência ao SLA. Sem configuração por
 * restaurante ainda — é um valor razoável de mercado para uma cozinha de
 * lanches/pratos rápidos; vira campo de configuração se algum dia precisar
 * variar por tenant. */
const KITCHEN_SLA_TARGET_MINUTES = 15;

export interface MonthBucket {
  key: string;
  label: string;
  orderCount: number;
  revenue: number;
}

export interface TopProduct {
  productName: string;
  quantity: number;
  revenue: number;
}

export interface DashboardMetrics {
  ordersToday: number;
  ordersThisMonth: number;
  averageTicket: number;
  tablesServedToday: number;
  openTablesRightNow: number;
  /** `null` quando ainda não há nenhuma comanda fechada para calcular a média. */
  avgTableTimeMinutes: number | null;
  closedCommandsSample: number;
  kitchenSlaTargetMinutes: number;
  kitchenAvgPrepMinutesToday: number | null;
  kitchenSlaComplianceTodayPct: number | null;
  kitchenSampleToday: number;
  monthlyTrend: MonthBucket[];
  topProducts: TopProduct[];
}

function isSameLocalDay(iso: string, reference: Date): boolean {
  const d = new Date(iso);
  return (
    d.getFullYear() === reference.getFullYear() &&
    d.getMonth() === reference.getMonth() &&
    d.getDate() === reference.getDate()
  );
}

function monthKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

const MONTH_LABEL_FORMATTER = new Intl.DateTimeFormat('pt-BR', { month: 'short' });

/**
 * Rótulos de mês curtos ("mar", "abr"...) para caber nas bandas estreitas de
 * um gráfico de 6 meses sem colidir (skill de dataviz: nunca deixar rótulo
 * cortado/sobreposto) — o ano só aparece uma vez, no primeiro mês e sempre
 * que ele muda (ex: "jan/27"), como em qualquer eixo de tendência mensal.
 */
function buildMonthBuckets(count: number, reference: Date): MonthBucket[] {
  const buckets: MonthBucket[] = [];
  let lastYear: number | null = null;
  for (let i = count - 1; i >= 0; i -= 1) {
    const d = new Date(reference.getFullYear(), reference.getMonth() - i, 1);
    const monthLabel = MONTH_LABEL_FORMATTER.format(d).replace('.', '');
    const label = d.getFullYear() !== lastYear ? `${monthLabel}/${String(d.getFullYear()).slice(-2)}` : monthLabel;
    lastYear = d.getFullYear();
    buckets.push({ key: monthKey(d), label, orderCount: 0, revenue: 0 });
  }
  return buckets;
}

function minutesBetween(startIso: string, endIso: string): number {
  return (new Date(endIso).getTime() - new Date(startIso).getTime()) / 60_000;
}

function average(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

function computeMetrics(orders: Order[], commands: Command[], kdsItems: KdsItem[]): DashboardMetrics {
  const now = new Date();
  const activeOrders = orders.filter((o) => o.status !== 'CANCELLED');

  const monthlyTrend = buildMonthBuckets(MONTHS_IN_TREND, now);
  const bucketByKey = new Map(monthlyTrend.map((bucket) => [bucket.key, bucket]));
  for (const order of activeOrders) {
    const bucket = bucketByKey.get(monthKey(new Date(order.created_at)));
    if (bucket) {
      bucket.orderCount += 1;
      bucket.revenue += order.total_amount;
    }
  }
  const ordersThisMonth = monthlyTrend[monthlyTrend.length - 1]?.orderCount ?? 0;
  const ordersToday = activeOrders.filter((o) => isSameLocalDay(o.created_at, now)).length;
  const averageTicket = average(activeOrders.map((o) => o.total_amount)) ?? 0;

  const productTotals = new Map<string, TopProduct>();
  for (const order of activeOrders) {
    for (const item of order.items) {
      const existing = productTotals.get(item.product_name) ?? {
        productName: item.product_name,
        quantity: 0,
        revenue: 0,
      };
      existing.quantity += item.quantity;
      existing.revenue += item.total_price;
      productTotals.set(item.product_name, existing);
    }
  }
  const topProducts = [...productTotals.values()].sort((a, b) => b.quantity - a.quantity).slice(0, 5);

  const tablesServedToday = commands.filter((c) => isSameLocalDay(c.opened_at, now)).length;
  const openTablesRightNow = commands.filter((c) => c.status === 'OPEN').length;

  const closedCommands = commands.filter(
    (c): c is Command & { closed_at: string } => c.status === 'CLOSED' && c.closed_at !== null,
  );
  const avgTableTimeMinutes = average(
    closedCommands.map((c) => minutesBetween(c.opened_at, c.closed_at)),
  );

  const itemsReadyToday = kdsItems.filter(
    (i): i is KdsItem & { ready_at: string } => i.ready_at !== null && isSameLocalDay(i.created_at, now),
  );
  const prepMinutesToday = itemsReadyToday.map((i) => minutesBetween(i.created_at, i.ready_at));
  const kitchenAvgPrepMinutesToday = average(prepMinutesToday);
  const kitchenSlaComplianceTodayPct =
    prepMinutesToday.length > 0
      ? (prepMinutesToday.filter((m) => m <= KITCHEN_SLA_TARGET_MINUTES).length / prepMinutesToday.length) * 100
      : null;

  return {
    ordersToday,
    ordersThisMonth,
    averageTicket,
    tablesServedToday,
    openTablesRightNow,
    avgTableTimeMinutes,
    closedCommandsSample: closedCommands.length,
    kitchenSlaTargetMinutes: KITCHEN_SLA_TARGET_MINUTES,
    kitchenAvgPrepMinutesToday,
    kitchenSlaComplianceTodayPct,
    kitchenSampleToday: itemsReadyToday.length,
    monthlyTrend,
    topProducts,
  };
}

/**
 * Métricas do dashboard completo do dono — agregadas no cliente combinando
 * `order-service` + `dining-service` + `kitchen-service`, seguindo o mesmo
 * padrão já usado em `useRevenue` (não existe um serviço de analytics/BI
 * dedicado; `analytics-service` hoje só tem `AuditLog`). Refeito a cada 30s.
 */
export function useDashboardMetrics(options?: { enabled?: boolean }) {
  return useQuery<DashboardMetrics>({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {
      const [orders, commands, kdsItems] = await Promise.all([
        listOrders(),
        listCommands(),
        listKdsItems(),
      ]);
      return computeMetrics(orders, commands, kdsItems);
    },
    enabled: options?.enabled ?? true,
    refetchInterval: DASHBOARD_POLL_INTERVAL_MS,
  });
}
