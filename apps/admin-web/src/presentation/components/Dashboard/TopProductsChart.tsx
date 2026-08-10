import React from 'react';
import type { TopProduct } from '../../hooks/useDashboardMetrics';

interface TopProductsChartProps {
  products: TopProduct[];
  /** Cor da série (hex) — slot 3 da paleta categórica validada (aqua), terceiro
   * contexto de magnitude simultâneo no mesmo dashboard (skill de dataviz). */
  color: string;
}

const ROW_HEIGHT = 28;
const BAR_THICKNESS = 16;
const LABEL_COLOR = '#565c6b'; // token `ink-soft`
const VALUE_COLOR = '#1b1e27'; // token `ink`

/**
 * Ranking horizontal dos produtos mais pedidos (por quantidade) — barras
 * horizontais porque nomes de produto variam muito em comprimento e não
 * cabem como rótulo de categoria embaixo de uma barra vertical.
 */
export const TopProductsChart: React.FC<TopProductsChartProps> = ({ products, color }) => {
  if (products.length === 0) {
    return (
      <div className="bg-surface rounded-xl p-4 border border-border shadow-sm">
        <h4 className="text-xs font-bold font-display text-ink mb-3">Produtos Mais Pedidos</h4>
        <p className="text-xs text-ink-soft">Ainda não há pedidos suficientes para um ranking.</p>
      </div>
    );
  }

  const maxQuantity = Math.max(...products.map((p) => p.quantity));
  const height = products.length * ROW_HEIGHT;
  const trackStart = 42; // espaço reservado ao nome do produto (%)

  return (
    <div className="bg-surface rounded-xl p-4 border border-border shadow-sm">
      <h4 className="text-xs font-bold font-display text-ink mb-3">Produtos Mais Pedidos</h4>
      <svg viewBox={`0 0 100 ${height}`} className="w-full" style={{ height }} role="img" aria-label="Produtos mais pedidos">
        {products.map((product, i) => {
          const y = i * ROW_HEIGHT;
          const rowCenter = y + ROW_HEIGHT / 2;
          const barMaxWidth = 100 - trackStart - 12;
          const barWidth = (product.quantity / maxQuantity) * barMaxWidth;
          return (
            <g key={product.productName}>
              <title>{`${product.productName}: ${product.quantity} unidade(s) • R$ ${product.revenue.toFixed(2)}`}</title>
              <text x={0} y={rowCenter + 2.5} fontSize={6.5} fill={LABEL_COLOR}>
                {product.productName.length > 22 ? `${product.productName.slice(0, 21)}…` : product.productName}
              </text>
              <rect
                x={trackStart}
                y={rowCenter - BAR_THICKNESS / 2 / 3.2}
                width={Math.max(barWidth, 1)}
                height={5}
                rx={2.5}
                fill={color}
              />
              <text x={trackStart + barWidth + 3} y={rowCenter + 2.5} fontSize={6.5} fontWeight={700} fill={VALUE_COLOR}>
                {product.quantity}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
