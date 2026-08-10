import React from 'react';
import { ShoppingBag, ChevronRight } from 'lucide-react';

interface FloatingCartBarProps {
  totalCartCount: number;
  totalCartPrice: number;
  onOpenCart: () => void;
}

export const FloatingCartBar: React.FC<FloatingCartBarProps> = ({
  totalCartCount,
  totalCartPrice,
  onOpenCart,
}) => {
  if (totalCartCount === 0) return null;

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 max-w-lg w-[92%] z-40">
      <div className="bg-gray-900 text-white rounded-2xl p-3.5 shadow-2xl flex items-center justify-between backdrop-blur-lg border border-gray-800 animate-slide-up">
        <div className="flex items-center gap-3">
          <div className="relative bg-red-600 text-white p-2.5 rounded-xl">
            <ShoppingBag className="w-5 h-5" />
            <span className="absolute -top-1.5 -right-1.5 bg-white text-red-600 text-[10px] font-extrabold w-5 h-5 rounded-full flex items-center justify-center border-2 border-gray-900">
              {totalCartCount}
            </span>
          </div>
          <div>
            <p className="text-xs text-gray-400">Total acumulado</p>
            <p className="text-base font-extrabold text-white">R$ {totalCartPrice.toFixed(2).replace('.', ',')}</p>
          </div>
        </div>

        <button
          onClick={onOpenCart}
          className="bg-red-600 hover:bg-red-500 text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow-lg flex items-center gap-1.5 transition-all"
        >
          <span>Ver Comanda</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
