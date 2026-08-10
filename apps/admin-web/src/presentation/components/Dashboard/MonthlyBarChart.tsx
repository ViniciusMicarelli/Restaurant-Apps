import React from 'react';

interface MonthlyBarChartProps {
  title: string;
  data: { label: string; value: number }[];
  /** Cor da série (hex) — paleta categórica validada (skill de dataviz):
   * slot 1 azul `#2a78d6` para contagens, slot 2 laranja `#eb6834` para
   * valores monetários, mantendo um hue fixo por gráfico (nunca por rank). */
  color: string;
  valueFormatter?: (value: number) => string;
}

const CHART_HEIGHT = 180;
const BAR_AREA_HEIGHT = 128;
const MAX_BAR_THICKNESS = 24;
const BAR_RADIUS = 4;
const AXIS_COLOR = '#dde0e6'; // token `border`
const LABEL_COLOR = '#565c6b'; // token `ink-soft`
const VALUE_COLOR = '#1b1e27'; // token `ink`
// Mês atual (sempre o último da janela de 6 meses) — precisa saltar do
// resto sem depender de eixo numérico (direção visual, 2026-08-10,
// docs/logs/2026-08-10.md Sessão 8: "o número que importa não se
// distinguia dos outros cinco").
const HIGHLIGHT_COLOR = '#c1541f'; // token `accent`

const defaultFormatter = (value: number): string => value.toLocaleString('pt-BR');

/**
 * Gráfico de barras verticais de uma série só (magnitude por mês) — sem
 * gridlines/eixo Y: cada barra já leva o valor rotulado na ponta (skill de
 * dataviz, marks-and-anatomy.md), então o eixo numérico seria redundante.
 * Sem legenda por ser série única (o título já diz o que é plotado). A
 * última barra (mês corrente) usa o acento de marca em vez da cor da
 * série, com o valor em destaque — é o único número que muda de agora em
 * diante, o resto é histórico fechado.
 */
export const MonthlyBarChart: React.FC<MonthlyBarChartProps> = ({
  title,
  data,
  color,
  valueFormatter = defaultFormatter,
}) => {
  const maxValue = Math.max(1, ...data.map((d) => d.value));
  const bandWidth = 100 / data.length;
  const barWidth = Math.min(MAX_BAR_THICKNESS, bandWidth * 0.6);
  const baselineY = BAR_AREA_HEIGHT;
  const lastIndex = data.length - 1;

  return (
    <div className="bg-surface rounded-xl p-4 border border-border shadow-sm">
      <h4 className="text-xs font-bold font-display text-ink mb-3">{title}</h4>
      <svg viewBox={`0 0 100 ${CHART_HEIGHT}`} className="w-full" style={{ height: CHART_HEIGHT }} role="img" aria-label={title}>
        <line x1={0} y1={baselineY} x2={100} y2={baselineY} stroke={AXIS_COLOR} strokeWidth={0.5} />
        {data.map((d, i) => {
          const isCurrent = i === lastIndex;
          const barColor = isCurrent ? HIGHLIGHT_COLOR : color;
          const bandCenter = bandWidth * i + bandWidth / 2;
          const barHeight = (d.value / maxValue) * (BAR_AREA_HEIGHT - 24);
          const barX = bandCenter - barWidth / 2;
          const barY = baselineY - barHeight;
          return (
            <g key={d.label}>
              <title>{`${d.label}: ${valueFormatter(d.value)}`}</title>
              {/* corpo com topo arredondado */}
              <rect
                x={barX}
                y={barY}
                width={barWidth}
                height={Math.max(barHeight, 1)}
                rx={BAR_RADIUS}
                fill={barColor}
                opacity={isCurrent ? 1 : 0.55}
              />
              {/* reforça a base quadrada por cima do arredondamento inferior do rect acima */}
              {barHeight > BAR_RADIUS && (
                <rect
                  x={barX}
                  y={baselineY - BAR_RADIUS}
                  width={barWidth}
                  height={BAR_RADIUS}
                  fill={barColor}
                  opacity={isCurrent ? 1 : 0.55}
                />
              )}
              {d.value > 0 && (
                <text
                  x={bandCenter}
                  y={barY - 4}
                  textAnchor="middle"
                  fontSize={isCurrent ? 7.5 : 6.5}
                  fontWeight={700}
                  fill={isCurrent ? HIGHLIGHT_COLOR : VALUE_COLOR}
                >
                  {valueFormatter(d.value)}
                </text>
              )}
              <text
                x={bandCenter}
                y={baselineY + 11}
                textAnchor="middle"
                fontSize={5.5}
                fontWeight={isCurrent ? 700 : 400}
                fill={isCurrent ? HIGHLIGHT_COLOR : LABEL_COLOR}
              >
                {d.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
