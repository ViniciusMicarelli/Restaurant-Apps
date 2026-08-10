import type React from 'react';

/**
 * Tom semântico do estado — separado do acento de marca (direção visual,
 * 2026-08-10, docs/logs/2026-08-10.md Sessão 8). `accent` é usado pra
 * "em uso normal" (mesa ocupada), nunca pra problema — isso deixa
 * `critical` livre exclusivamente pra estados que realmente pedem atenção
 * (ex: ticket de KDS atrasado), em vez de competir visualmente com "mesa
 * ocupada" (que não é um problema).
 */
export type StatusTone = 'good' | 'accent' | 'warning' | 'critical' | 'info';

const STRIPE_CLASS: Record<StatusTone, string> = {
  good: 'before:bg-good',
  accent: 'before:bg-accent',
  warning: 'before:bg-warning',
  critical: 'before:bg-critical',
  info: 'before:bg-info',
};

const PILL_CLASS: Record<StatusTone, string> = {
  good: 'bg-good-soft text-good',
  accent: 'bg-accent-soft text-accent',
  warning: 'bg-warning-soft text-warning',
  critical: 'bg-critical-soft text-critical',
  info: 'bg-info-soft text-info',
};

const DOT_CLASS: Record<StatusTone, string> = {
  good: 'bg-good',
  accent: 'bg-accent',
  warning: 'bg-warning',
  critical: 'bg-critical',
  info: 'bg-info',
};

/** Faixa de 4px na borda esquerda de um card — aplicar junto de
 * `relative overflow-hidden` no elemento pai (a faixa usa `::before`
 * posicionado absoluto). Reconhecível à distância, sem precisar ler o
 * texto do card (mapa de mesas, tickets de KDS). */
export function statusStripeClassName(tone: StatusTone): string {
  return `relative overflow-hidden before:content-[''] before:absolute before:inset-y-0 before:left-0 before:w-1 ${STRIPE_CLASS[tone]}`;
}

interface StatusPillProps {
  tone: StatusTone;
  label: string;
  className?: string;
}

/** Pill com ponto colorido — usado junto da faixa lateral (`statusStripeClassName`)
 * pra reforçar o mesmo estado de duas formas (cor + forma), não só cor
 * (heurística de acessibilidade: nunca só cor pra transmitir estado). */
export const StatusPill: React.FC<StatusPillProps> = ({ tone, label, className = '' }) => (
  <span
    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${PILL_CLASS[tone]} ${className}`}
  >
    <span className={`h-1.5 w-1.5 rounded-full ${DOT_CLASS[tone]}`} aria-hidden="true" />
    {label}
  </span>
);
