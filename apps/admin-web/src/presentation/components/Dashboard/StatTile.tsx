import React from 'react';
import type { StatusTone } from '../StatusBadge/StatusBadge';

type Tone = 'default' | StatusTone;

interface StatTileProps {
  label: string;
  value: string;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
  /** Cor reservada de status (skill de dataviz) — nunca reaproveitada como
   * "mais uma série"; usada só quando o número em si é bom/ruim (ex: SLA). */
  tone?: Tone;
}

const TONE_ICON_CLASS: Record<Tone, string> = {
  default: 'text-ink-soft',
  good: 'text-good',
  warning: 'text-warning',
  critical: 'text-critical',
  accent: 'text-accent',
  info: 'text-info',
};

/** Stat tile padrão do dashboard: label + valor em destaque + dica opcional.
 * Valor usa a fonte de dado (`font-data`, tabular) — números ganham um
 * registro visual próprio, separado dos rótulos (direção visual,
 * 2026-08-10, docs/logs/2026-08-10.md Sessão 8). */
export const StatTile: React.FC<StatTileProps> = ({ label, value, hint, icon: Icon, tone = 'default' }) => (
  <div className="bg-surface rounded-xl p-4 border border-border shadow-sm">
    <div className="flex items-center justify-between text-ink-soft mb-2">
      <span className="text-xs font-semibold">{label}</span>
      <Icon className={`w-4 h-4 ${TONE_ICON_CLASS[tone]}`} />
    </div>
    <p className="text-xl font-bold font-data tabular-nums text-ink">{value}</p>
    {hint && <p className="text-[10px] text-ink-soft mt-1">{hint}</p>}
  </div>
);
