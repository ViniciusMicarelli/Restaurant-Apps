import React, { useEffect, useMemo, useState } from 'react';
import QRCode from 'qrcode';
import { Copy, Check } from 'lucide-react';

interface CustomerPixPanelProps {
  totalAmount: number;
  isSubmitting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Payload "copia e cola" só pra parecer uma tela de Pix de verdade — não é
 * um BR Code (EMV) válido. Mesma simulação do `PixPaymentPanel` do
 * `admin-web`: o `payment-service` não tem integração com nenhum PSP. */
function buildFakePixPayload(totalAmount: number): string {
  const random = Math.random().toString(36).slice(2, 10).toUpperCase();
  return `00020126PIXSIMULADO${random}520400005303986540${totalAmount.toFixed(2)}5802BR6009RESTAURANTE`;
}

/** Tela de Pix do autoatendimento (US-05.4) — o cliente "autentica" no
 * próprio app do banco, por isso não pede assinatura nem dados de cartão. */
export const CustomerPixPanel: React.FC<CustomerPixPanelProps> = ({
  totalAmount,
  isSubmitting,
  onConfirm,
  onCancel,
}) => {
  const [qrImage, setQrImage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const payload = useMemo(() => buildFakePixPayload(totalAmount), [totalAmount]);

  useEffect(() => {
    void QRCode.toDataURL(payload, { margin: 1, width: 200 }).then(setQrImage);
  }, [payload]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(payload);
    setCopied(true);
    setTimeout(() => setCopied(false), 2_000);
  };

  return (
    <div className="space-y-4">
      <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
        Simulação — sem gateway Pix real. Em produção, o QR/chave viriam de um provedor de pagamento de verdade.
      </p>

      <div className="flex justify-center">
        {qrImage ? (
          <img src={qrImage} alt="QR Code Pix (simulado)" className="rounded-xl" />
        ) : (
          <div className="w-[200px] h-[200px] bg-gray-50 rounded-xl animate-pulse" />
        )}
      </div>

      <button
        type="button"
        onClick={handleCopy}
        className="w-full flex items-center justify-center gap-2 text-[11px] font-mono bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-gray-600 hover:bg-gray-100 break-all"
      >
        {copied ? <Check className="w-3.5 h-3.5 shrink-0 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 shrink-0" />}
        <span className="truncate">{payload}</span>
      </button>

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
          type="button"
          onClick={onConfirm}
          disabled={isSubmitting}
          className="flex-1 bg-red-600 disabled:bg-red-300 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-md"
        >
          {isSubmitting ? 'Processando...' : 'Já paguei pelo Pix'}
        </button>
      </div>
    </div>
  );
};
