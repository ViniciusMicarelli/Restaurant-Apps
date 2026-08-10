import React, { useMemo, useState } from 'react';
import { CreditCard } from 'lucide-react';

export interface CustomerCardResult {
  cardLast4: string;
  cardHolderName: string;
}

interface CustomerCardFormProps {
  totalAmount: number;
  isSubmitting: boolean;
  onSubmit: (result: CustomerCardResult) => void;
  onCancel: () => void;
}

function clampDigits(value: string, maxLen: number): string {
  return value.replace(/\D/g, '').slice(0, maxLen);
}

function formatNumberSpaces(num: string): string {
  return num.replace(/(\d{4})(?=\d)/g, '$1 ');
}

/**
 * Cartão fake do autoatendimento (US-05.4) — mesmo cartão visual/simulado do
 * `PaymentSignatureForm` do `admin-web`, sem o bloco de assinatura: essa
 * etapa existe lá como evidência de conferência do garçom no fechamento
 * presencial, e não se aplica a um pagamento que o próprio cliente faz
 * sozinho no celular. PAN completo e CVV nunca saem deste formulário — só
 * os 4 últimos dígitos e o nome do titular.
 */
export const CustomerCardForm: React.FC<CustomerCardFormProps> = ({
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

  const years = useMemo(() => {
    const start = new Date().getFullYear();
    return Array.from({ length: 10 }, (_, i) => String(start + i));
  }, []);

  const numberValid = number.length >= 13;
  const holderValid = holder.trim().length >= 2;
  const monthValid = Boolean(month);
  const yearValid = Boolean(year);
  const cvvValid = /^\d{3,4}$/.test(cvv);
  const allValid = numberValid && holderValid && monthValid && yearValid && cvvValid;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!allValid) return;
    onSubmit({ cardLast4: number.slice(-4), cardHolderName: holder.trim() });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
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

      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
        <span className="text-xs font-semibold text-gray-500">Total a pagar</span>
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
          {isSubmitting ? 'Processando...' : 'Pagar agora'}
        </button>
      </div>
    </form>
  );
};
