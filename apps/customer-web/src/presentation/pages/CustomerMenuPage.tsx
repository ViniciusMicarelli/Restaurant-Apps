import React, { useState, useEffect, useMemo } from 'react';
import { Search, Check, Info, AlertTriangle, ClipboardList, ShieldAlert } from 'lucide-react';
import { Header } from '../components/Header/Header';
import { CategoryCarousel } from '../components/CategoryCarousel/CategoryCarousel';
import { ProductCard } from '../components/ProductCard/ProductCard';
import { FloatingCartBar } from '../components/FloatingCartBar/FloatingCartBar';
import { MyOrdersPanel } from '../components/MyOrdersPanel/MyOrdersPanel';
import { defaultBranding } from '../../domain/entities/branding';
import { applyBrandingToDOM } from '../../theme/branding';
import { useRestaurant } from '../hooks/useRestaurant';
import { useCategories, useProducts } from '../hooks/useMenu';
import { useTableAccess } from '../hooks/useTableAccess';
import { RiveLoadingIndicator } from '../components/Rive/RiveLoadingIndicator';

const ALL_CATEGORY_ID = 'all';

export const CustomerMenuPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>(ALL_CATEGORY_ID);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [cart, setCart] = useState<{ [productId: string]: number }>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [showMyOrders, setShowMyOrders] = useState(false);

  const restaurantQuery = useRestaurant();
  const tenantId = restaurantQuery.data?.id;
  const { tableNumber, secret: tableSecret, status: tableAccessStatus } = useTableAccess(tenantId);
  const categoriesQuery = useCategories(tenantId);
  const productsQuery = useProducts(tenantId);

  const branding = restaurantQuery.data?.branding ?? defaultBranding;

  useEffect(() => {
    applyBrandingToDOM(branding);
  }, [branding]);

  const triggerToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleAddToCart = (productId: string, name: string) => {
    setCart((prev) => ({ ...prev, [productId]: (prev[productId] || 0) + 1 }));
    triggerToast(`"${name}" adicionado ao pedido!`);
  };

  const categories = useMemo(
    () => [{ id: ALL_CATEGORY_ID, name: 'Todos os Pratos', icon: '✨', display_order: -1 }, ...(categoriesQuery.data ?? [])],
    [categoriesQuery.data],
  );

  const filteredProducts = (productsQuery.data ?? []).filter((product) => {
    const matchesCategory = selectedCategory === ALL_CATEGORY_ID || product.category_id === selectedCategory;
    const q = searchQuery.toLowerCase().trim();
    if (!q) return matchesCategory;

    const matchesName = product.name.toLowerCase().includes(q);
    const matchesDesc = product.description.toLowerCase().includes(q);
    return matchesCategory && (matchesName || matchesDesc);
  });

  const totalCartCount = Object.values(cart).reduce((a, b) => a + b, 0);
  const totalCartPrice = Object.entries(cart).reduce((sum, [id, qty]) => {
    const product = productsQuery.data?.find((p) => p.id === id);
    return sum + (product ? product.price * qty : 0);
  }, 0);

  if (!restaurantQuery.isLoading && restaurantQuery.isError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 font-sans px-4">
        <div className="bg-white rounded-2xl p-8 text-center border border-gray-100 max-w-sm">
          <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-3" />
          <p className="text-sm font-semibold text-gray-800">Não foi possível carregar o cardápio</p>
          <p className="text-xs text-gray-500 mt-1">
            Verifique se o link do QR Code inclui o restaurante correto (<code>?r=slug-do-restaurante</code>).
          </p>
        </div>
      </div>
    );
  }

  // QR Code rotativo por mesa é obrigatório — sem uma secret válida da mesa
  // atual (gerada no admin-web, válida até a comanda ser encerrada) o
  // cardápio não abre.
  if (tenantId && tableAccessStatus === 'denied') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 font-sans px-4">
        <div className="bg-white rounded-2xl p-8 text-center border border-gray-100 max-w-sm">
          <ShieldAlert className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-sm font-semibold text-gray-800">QR Code inválido ou expirado</p>
          <p className="text-xs text-gray-500 mt-1">
            Peça a um garçom para gerar um novo QR Code da sua mesa e escaneie novamente.
          </p>
        </div>
      </div>
    );
  }

  if (tenantId && tableAccessStatus === 'checking') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3 bg-gray-100 font-sans">
        <RiveLoadingIndicator size={96} />
        <p className="text-sm text-gray-500">Validando QR Code da mesa...</p>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen flex flex-col font-sans pb-24 transition-colors duration-300"
      style={{ backgroundColor: 'var(--brand-bg)' }}
    >
      {toastMessage && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-gray-900 text-white text-sm font-medium px-4 py-2.5 rounded-full shadow-2xl flex items-center gap-2 animate-bounce">
          <Check className="w-4 h-4 text-emerald-400" />
          {toastMessage}
        </div>
      )}

      <Header
        branding={branding}
        restaurantName={restaurantQuery.data?.trade_name ?? 'Carregando...'}
        tableNumber={tableNumber}
      />

      <div className="max-w-2xl mx-auto w-full px-4 mt-4">
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar pratos, hambúrgueres ou bebidas..."
            className="w-full bg-white pl-11 pr-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 shadow-sm transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-1 rounded-md"
            >
              Limpar
            </button>
          )}
        </div>

        <div className="mt-4">
          <CategoryCarousel
            categories={categories}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
          />
        </div>

        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
              {selectedCategory === ALL_CATEGORY_ID
                ? 'Cardápio Principal'
                : categories.find((c) => c.id === selectedCategory)?.name}
            </h2>
            <span className="text-xs text-gray-500 font-medium">{filteredProducts.length} itens encontrados</span>
          </div>

          {productsQuery.isLoading && (
            <div className="flex flex-col items-center gap-2 py-6">
              <RiveLoadingIndicator size={72} />
              <p className="text-sm text-gray-500">Carregando cardápio...</p>
            </div>
          )}

          {!productsQuery.isLoading && filteredProducts.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 text-center border border-gray-100">
              <Info className="w-10 h-10 text-gray-300 mx-auto mb-2" />
              <p className="text-sm font-semibold text-gray-800">Nenhum prato encontrado</p>
              <p className="text-xs text-gray-500 mt-1">Tente buscar por outro termo ou categoria.</p>
            </div>
          ) : (
            filteredProducts.map((product) => (
              <ProductCard key={product.id} product={product} onAddToCart={handleAddToCart} />
            ))
          )}
        </div>
      </div>

      {tableNumber && (
        <button
          onClick={() => setShowMyOrders(true)}
          className="fixed top-4 right-4 z-30 flex items-center gap-1.5 bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-full shadow-lg"
        >
          <ClipboardList className="w-3.5 h-3.5" />
          Meu Pedido
        </button>
      )}

      {showMyOrders && (
        <MyOrdersPanel
          tenantId={tenantId}
          tableNumber={tableNumber}
          secret={tableSecret}
          serviceFeePercent={restaurantQuery.data?.service_fee_percent ?? 0}
          onClose={() => setShowMyOrders(false)}
        />
      )}

      <FloatingCartBar
        totalCartCount={totalCartCount}
        totalCartPrice={totalCartPrice}
        onOpenCart={() => triggerToast('Fechamento de comanda ainda não disponível neste cardápio.')}
      />
    </div>
  );
};
