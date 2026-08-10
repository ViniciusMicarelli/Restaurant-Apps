import React from 'react';
import { LayoutDashboard, UtensilsCrossed, ChefHat, Palette, Lock, Wallet } from 'lucide-react';
import { useSessionStore } from '../../../infrastructure/state/sessionStore';

export type AdminTab = 'dashboard' | 'tables' | 'kds' | 'branding' | 'revenue';

interface SidebarProps {
  activeTab: AdminTab;
  onSelectTab: (tab: AdminTab) => void;
}

interface NavItem {
  tab: AdminTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  /** `undefined` = visível para qualquer papel autenticado. */
  roles?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { tab: 'dashboard', label: 'Visão Geral & Vendas', icon: LayoutDashboard },
  { tab: 'tables', label: 'Mapa de Mesas (Salão)', icon: UtensilsCrossed },
  { tab: 'kds', label: 'Monitor KDS da Cozinha', icon: ChefHat },
  // Faturamento é informação financeira sensível — só o dono vê (primeiro
  // caso de navegação restrita por papel no admin-web).
  { tab: 'revenue', label: 'Faturamento', icon: Wallet, roles: ['RESTAURANT_OWNER'] },
  { tab: 'branding', label: 'Tema White-Label', icon: Palette },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const user = useSessionStore((state) => state.user);
  const logout = useSessionStore((state) => state.logout);
  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col justify-between p-4 shadow-xl">
      <div>
        <div className="flex items-center gap-3 px-2 py-3 mb-6 border-b border-gray-800">
          <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center font-black text-xl shadow-lg shadow-red-500/30">
            R
          </div>
          <div>
            <h1 className="text-sm font-bold leading-tight">Burger House</h1>
            <p className="text-[11px] text-gray-400">Painel do Gestor (SaaS)</p>
          </div>
        </div>

        <nav className="space-y-1.5">
          {visibleItems.map(({ tab, label, icon: Icon }) => (
            <button
              key={tab}
              onClick={() => onSelectTab(tab)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === tab ? 'bg-red-600 text-white shadow-md' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      <div className="bg-gray-800 rounded-xl p-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-xs font-bold">
            {(user?.name ?? '?').slice(0, 2).toUpperCase()}
          </div>
          <div>
            <p className="text-xs font-bold">{user?.name ?? 'Usuário'}</p>
            <p className="text-[10px] text-emerald-400 font-medium">{user?.role ?? ''}</p>
          </div>
        </div>
        <button onClick={logout} title="Sair" aria-label="Sair">
          <Lock className="w-4 h-4 text-gray-400 hover:text-white cursor-pointer" />
        </button>
      </div>
    </aside>
  );
};
