import React, { useEffect } from 'react';
// `Rive` (o componente React) é o export default — ver nota em RiveLoadingIndicator.tsx.
import RiveComponent, { Fit, Layout } from '@rive-app/react-canvas';

const CONTAIN_LAYOUT = new Layout({ fit: Fit.Contain });

interface PaymentSuccessCelebrationProps {
  message: string;
  onDone: () => void;
  durationMs?: number;
}

/**
 * Celebração de sucesso (Rive) mostrada ao fechar uma comanda com pagamento
 * aprovado — mesmo asset/ideia do `RivePaymentReward` do `waiter-mobile`
 * (`rewards.riv`), aqui sem data-binding (autoplay simples) pra manter o
 * lado web mais enxuto. Fecha sozinha depois de `durationMs`.
 */
export const PaymentSuccessCelebration: React.FC<PaymentSuccessCelebrationProps> = ({
  message,
  onDone,
  durationMs = 2200,
}) => {
  useEffect(() => {
    const timer = setTimeout(onDone, durationMs);
    return () => clearTimeout(timer);
  }, [onDone, durationMs]);

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/45">
      <div className="bg-white rounded-2xl shadow-2xl p-6 flex flex-col items-center gap-3 max-w-xs">
        <div style={{ width: 160, height: 160 }}>
          <RiveComponent src="/animations/rewards.riv" layout={CONTAIN_LAYOUT} />
        </div>
        <p className="text-sm font-semibold text-gray-900 text-center whitespace-pre-line">{message}</p>
      </div>
    </div>
  );
};
