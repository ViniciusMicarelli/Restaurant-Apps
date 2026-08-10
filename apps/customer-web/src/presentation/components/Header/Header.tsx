import React from 'react';
import { QrCode } from 'lucide-react';
import { RestaurantBranding } from '../../../domain/entities/branding';

interface HeaderProps {
  branding: RestaurantBranding;
  restaurantName: string;
  tableNumber: number | null;
}

export const Header: React.FC<HeaderProps> = ({ branding, restaurantName, tableNumber }) => {
  return (
    <div>
      {/* Banner de Capa */}
      <div className="relative h-44 sm:h-56 w-full overflow-hidden">
        <img
          src={branding.banner_url}
          alt="Banner do Restaurante"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
      </div>

      {/* Header Info Card */}
      <div className="max-w-2xl mx-auto w-full px-4 -mt-10 relative z-10">
        <div className="bg-white rounded-2xl p-4 shadow-xl border border-gray-100 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3.5 min-w-0">
            <img
              src={branding.logo_url}
              alt="Logo"
              className="w-14 h-14 rounded-xl object-cover shadow-md border border-gray-100"
            />
            <div className="min-w-0">
              <h1 className="text-lg font-bold text-gray-900 leading-tight truncate">{restaurantName}</h1>
              <p className="text-xs text-gray-500 mt-1">Cardápio digital</p>
            </div>
          </div>

          {tableNumber !== null && (
            <div className="bg-red-50 text-red-700 px-3 py-1.5 rounded-xl flex items-center gap-1.5 text-xs font-bold border border-red-100 shrink-0">
              <QrCode className="w-3.5 h-3.5" />
              Mesa {tableNumber}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
