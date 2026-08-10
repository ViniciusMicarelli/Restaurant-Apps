import React, { useEffect, useState } from 'react';

const WARNING_THRESHOLD_MS = 5 * 60 * 1000; // 5 min — item começa a demorar
const DANGER_THRESHOLD_MS = 10 * 60 * 1000; // 10 min — item atrasado

export type ElapsedUrgency = 'normal' | 'warning' | 'critical';

/** Mesmos limiares usados pelo cronômetro abaixo — exportado pra quem
 * precisar decidir a faixa/pill do card inteiro (não só a cor do texto do
 * tempo), ex: o card de ticket do KDS. */
export function getElapsedUrgency(elapsedMs: number): ElapsedUrgency {
  if (elapsedMs >= DANGER_THRESHOLD_MS) return 'critical';
  if (elapsedMs >= WARNING_THRESHOLD_MS) return 'warning';
  return 'normal';
}

function formatElapsed(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes === 0) return `há ${seconds}s`;
  return `há ${minutes}min ${seconds}s`;
}

/**
 * Cronômetro "há quanto tempo" ao vivo — recalcula a cada segundo no
 * cliente a partir de `createdAt` (não depende de nenhum push do backend).
 * Muda de cor conforme o item vai ficando parado na esteira, para chamar
 * atenção da cozinha para itens atrasados.
 */
export const ElapsedTime: React.FC<{ createdAt: string; className?: string }> = ({
  createdAt,
  className = '',
}) => {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1_000);
    return () => clearInterval(timer);
  }, []);

  const elapsedMs = now - new Date(createdAt).getTime();
  const urgency = getElapsedUrgency(elapsedMs);
  const colorClass =
    urgency === 'critical' ? 'text-critical' : urgency === 'warning' ? 'text-warning' : 'text-ink-soft';

  return (
    <span className={`text-[11px] font-bold tabular-nums ${colorClass} ${className}`}>
      {formatElapsed(elapsedMs)}
    </span>
  );
};
