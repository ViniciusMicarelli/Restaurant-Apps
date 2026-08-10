import React from 'react';
import { Plus } from 'lucide-react';
import { Product } from '../../../domain/entities/product';

interface ProductCardProps {
  product: Product;
  onAddToCart: (productId: string, productName: string) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onAddToCart }) => {
  return (
    <div className="bg-surface rounded-2xl p-3.5 border border-border shadow-sm hover:shadow-md transition-all flex gap-3.5 items-center group">
      {product.photo_url && (
        <img
          src={product.photo_url}
          alt={product.name}
          className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl object-cover flex-shrink-0 group-hover:scale-105 transition-transform"
        />
      )}

      <div className="flex-1 min-w-0">
        {/* Registro tipográfico próprio do cardápio — serifa itálica só
            aqui, a única leitura feita por prazer, não sob pressão
            (direção visual, 2026-08-10, docs/logs/2026-08-10.md Sessão 8). */}
        <h3 className="font-menu italic text-base text-ink leading-snug truncate">{product.name}</h3>
        <p className="text-xs text-ink-soft line-clamp-2 mt-1 leading-relaxed">{product.description}</p>

        <div className="mt-2.5 flex items-center justify-between">
          <span className="font-data tabular-nums text-base font-semibold text-accent">
            R$ {product.price.toFixed(2).replace('.', ',')}
          </span>

          <button
            onClick={() => onAddToCart(product.id, product.name)}
            className="bg-accent hover:brightness-95 active:scale-95 text-white p-2 rounded-xl shadow-md shadow-black/10 transition-all flex items-center gap-1 text-xs font-semibold"
          >
            <Plus className="w-4 h-4" />
            <span>Adicionar</span>
          </button>
        </div>
      </div>
    </div>
  );
};
