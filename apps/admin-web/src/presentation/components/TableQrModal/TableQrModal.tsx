import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import { X, Copy, Check, RefreshCw } from 'lucide-react';
import { rotateTableQrSecret, type Table } from '../../../infrastructure/api/diningApi';

interface TableQrModalProps {
  table: Table;
  restaurantSlug: string;
  onClose: () => void;
}

/**
 * QR Code rotativo por mesa — obrigatório para o cardápio digital abrir
 * (`customer-web` valida a secret antes de carregar qualquer coisa). Gera
 * uma secret ao abrir o modal e ela permanece válida durante todo o ciclo de
 * atendimento da mesa — quem já saiu não consegue reaproveitá-la, porque
 * `CloseCommandUseCase` rotaciona a secret sozinho quando a comanda é
 * encerrada (não há mais expiração por tempo curto/auto-refresh aqui).
 */
export const TableQrModal: React.FC<TableQrModalProps> = ({ table, restaurantSlug, onClose }) => {
  const [qrImage, setQrImage] = useState<string | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [isRotating, setIsRotating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rotate = async () => {
    try {
      setIsRotating(true);
      setError(null);
      const { secret } = await rotateTableQrSecret(table.id);
      const customerWebUrl = import.meta.env.VITE_CUSTOMER_WEB_URL;
      const fullUrl = `${customerWebUrl}/?r=${restaurantSlug}&table=${table.number}&secret=${secret}`;
      setUrl(fullUrl);
      const dataUrl = await QRCode.toDataURL(fullUrl, { margin: 1, width: 220 });
      setQrImage(dataUrl);
    } catch {
      setError('Falha ao gerar o QR Code. Tente novamente.');
    } finally {
      setIsRotating(false);
    }
  };

  useEffect(() => {
    void rotate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [table.id]);

  const handleCopy = async () => {
    if (!url) return;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2_000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-gray-900">QR Code — Mesa {table.number}</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && <p className="text-xs text-red-600 mb-3">{error}</p>}

        {qrImage ? (
          <img src={qrImage} alt={`QR Code da Mesa ${table.number}`} className="mx-auto rounded-xl" />
        ) : (
          <div className="w-[220px] h-[220px] mx-auto flex items-center justify-center bg-gray-50 rounded-xl">
            <p className="text-xs text-gray-400">Gerando...</p>
          </div>
        )}

        <p className="text-[11px] font-semibold text-gray-500 mt-3">
          Válido durante todo o atendimento desta mesa — gera um código novo
          automaticamente quando a comanda for encerrada
        </p>

        {url && (
          <button
            onClick={handleCopy}
            className="mt-4 w-full flex items-center justify-center gap-2 text-[11px] font-mono bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-gray-600 hover:bg-gray-100 break-all"
          >
            {copied ? <Check className="w-3.5 h-3.5 shrink-0 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 shrink-0" />}
            <span className="truncate">{url}</span>
          </button>
        )}

        <button
          onClick={() => void rotate()}
          disabled={isRotating}
          className="mt-2 w-full flex items-center justify-center gap-2 text-[11px] font-semibold text-gray-500 hover:text-gray-700 disabled:opacity-50 px-3 py-2"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRotating ? 'animate-spin' : ''}`} />
          Gerar novo código (invalida o atual)
        </button>
      </div>
    </div>
  );
};
