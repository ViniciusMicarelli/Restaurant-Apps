import React, { useMemo, useRef, useState } from 'react';
import { CreditCard, PenLine, RotateCcw } from 'lucide-react';

export interface PaymentSignatureResult {
  cardLast4: string;
  cardHolderName: string;
  signatureData: string;
}

interface PaymentSignatureFormProps {
  totalAmount: number;
  isSubmitting: boolean;
  onSubmit: (result: PaymentSignatureResult) => void;
  onCancel: () => void;
}

function clampDigits(value: string, maxLen: number): string {
  return value.replace(/\D/g, '').slice(0, maxLen);
}

function formatNumberSpaces(num: string): string {
  return num.replace(/(\d{4})(?=\d)/g, '$1 ');
}

/**
 * Pagamento fake (cartão simulado, sem gateway real — já é assim no backend
 * hoje) + captura de assinatura do cliente, combinados numa única tela de
 * fechamento de comanda. O PAN completo e o CVV nunca saem do formulário:
 * só os 4 últimos dígitos + nome do titular são enviados para o backend, só
 * para exibir num recibo depois.
 *
 * Assinatura é um `<canvas>` nativo (sem `@ark-ui/react`, que não está
 * instalado no projeto) exportado como PNG base64 via `toDataURL()`.
 */
export const PaymentSignatureForm: React.FC<PaymentSignatureFormProps> = ({
  totalAmount,
  isSubmitting,
  onSubmit,
  onCancel,
}) => {
  const [number, setNumber] = useState('');
  const [holder, setHolder] = useState('');
  const [month, setMonth] = useState('');
  const [year, setYear] = useState('');
  const [cvv, setCvv] = useState('');
  const [flip, setFlip] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);

  const years = useMemo(() => {
    const start = new Date().getFullYear();
    return Array.from({ length: 10 }, (_, i) => String(start + i));
  }, []);

  const numberValid = number.length >= 13;
  const holderValid = holder.trim().length >= 2;
  const monthValid = Boolean(month);
  const yearValid = Boolean(year);
  const cvvValid = /^\d{3,4}$/.test(cvv);
  const allValid = numberValid && holderValid && monthValid && yearValid && cvvValid && hasSignature;

  const getCanvasPoint = (event: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  };

  const handlePointerDown = (event: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    setIsDrawing(true);
    const { x, y } = getCanvasPoint(event);
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const handlePointerMove = (event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;
    const { x, y } = getCanvasPoint(event);
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#111827';
    ctx.lineTo(x, y);
    ctx.stroke();
    setHasSignature(true);
  };

  const handlePointerUp = () => setIsDrawing(false);

  const clearSignature = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (canvas && ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!allValid || !canvasRef.current) return;
    onSubmit({
      cardLast4: number.slice(-4),
      cardHolderName: holder.trim(),
      signatureData: canvasRef.current.toDataURL('image/png'),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Cartão (visual) */}
      <div
        className="relative w-full h-44 rounded-2xl p-5 text-white shadow-lg overflow-hidden transition-transform duration-500"
        style={{
          background: 'linear-gradient(to right bottom, #323941, #061018)',
          transform: flip ? 'rotateY(180deg)' : 'none',
          transformStyle: 'preserve-3d',
        }}
      >
        <div style={{ backfaceVisibility: 'hidden', display: flip ? 'none' : 'block' }}>
          <div className="flex items-center justify-between mb-6">
            <CreditCard className="w-6 h-6 opacity-80" />
            <span className="text-[10px] font-bold uppercase tracking-wider opacity-70">Cartão Fake</span>
          </div>
          <p className="text-lg font-mono tracking-widest mb-6">
            {formatNumberSpaces(number).padEnd(19, '#')}
          </p>
          <div className="flex items-center justify-between text-xs">
            <div>
              <p className="opacity-60 text-[9px] uppercase mb-0.5">Titular</p>
              <p className="font-semibold uppercase">{holder || 'NOME NO CARTÃO'}</p>
            </div>
            <div>
              <p className="opacity-60 text-[9px] uppercase mb-0.5">Validade</p>
              <p className="font-semibold">
                {month || 'MM'}/{year ? year.slice(-2) : 'AA'}
              </p>
            </div>
          </div>
        </div>
        <div
          className="absolute inset-0 p-5 flex flex-col items-end justify-center"
          style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)', display: flip ? 'flex' : 'none' }}
        >
          <p className="text-[10px] font-bold uppercase opacity-70 mb-1">CVV</p>
          <div className="bg-white text-gray-900 rounded-lg px-3 py-1.5 text-sm font-mono w-20 text-right">
            {'*'.repeat(cvv.length)}
          </div>
        </div>
      </div>

      <div>
        <label className="text-xs font-semibold text-gray-700 block mb-1">Número do Cartão</label>
        <input
          inputMode="numeric"
          placeholder="1234 5678 9012 3456"
          value={formatNumberSpaces(number)}
          onChange={(e) => setNumber(clampDigits(e.target.value, 16))}
          onFocus={() => setFlip(false)}
          className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-sm"
        />
      </div>

      <div>
        <label className="text-xs font-semibold text-gray-700 block mb-1">Nome do Titular</label>
        <input
          placeholder="NOME COMPLETO"
          value={holder}
          onChange={(e) => setHolder(e.target.value.toUpperCase())}
          onFocus={() => setFlip(false)}
          className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-sm"
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs font-semibold text-gray-700 block mb-1">Mês</label>
          <select
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            onFocus={() => setFlip(false)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-2 py-2.5 text-sm"
          >
            <option value="">MM</option>
            {Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0')).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-gray-700 block mb-1">Ano</label>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            onFocus={() => setFlip(false)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-2 py-2.5 text-sm"
          >
            <option value="">AAAA</option>
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-gray-700 block mb-1">CVV</label>
          <input
            inputMode="numeric"
            placeholder="***"
            value={cvv}
            onChange={(e) => setCvv(clampDigits(e.target.value, 4))}
            onFocus={() => setFlip(true)}
            onBlur={() => setFlip(false)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-sm"
          />
        </div>
      </div>

      {/* Assinatura */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-semibold text-gray-700 flex items-center gap-1">
            <PenLine className="w-3.5 h-3.5" />
            Assinatura do cliente
          </label>
          <button
            type="button"
            onClick={clearSignature}
            className="text-[11px] font-semibold text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Limpar
          </button>
        </div>
        <canvas
          ref={canvasRef}
          width={400}
          height={120}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          className="w-full h-28 bg-gray-50 rounded-xl border border-dashed border-gray-300 touch-none"
        />
        <p className="text-[10px] text-gray-400 mt-1">
          {hasSignature ? '✓ Assinado' : 'Assine no campo acima com o mouse/dedo'}
        </p>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
        <span className="text-xs font-semibold text-gray-500">Total a cobrar</span>
        <span className="text-lg font-extrabold text-gray-900">R$ {totalAmount.toFixed(2)}</span>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 text-xs font-bold text-gray-600 bg-gray-100 hover:bg-gray-200 px-4 py-2.5 rounded-xl"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={!allValid || isSubmitting}
          className="flex-1 bg-red-600 disabled:bg-red-300 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-md"
        >
          {isSubmitting ? 'Processando...' : 'Confirmar Pagamento'}
        </button>
      </div>
    </form>
  );
};
