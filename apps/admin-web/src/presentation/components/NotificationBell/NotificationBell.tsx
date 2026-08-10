import React, { useState } from 'react';
import { Bell } from 'lucide-react';
import { useNotifications } from '../../hooks/useNotifications';
import { ElapsedTime } from '../ElapsedTime/ElapsedTime';

/**
 * Sino de notificações real (antes era só um ícone decorativo com uma
 * bolinha fixa) — busca `GET /api/v1/notifications` (notification-service)
 * a cada 5s. Continua simulado do lado do "envio" (sem provedor de
 * e-mail/WhatsApp real), mas agora reflete de verdade os eventos do sistema
 * (hoje: pedido pronto).
 */
export const NotificationBell: React.FC = () => {
  const [open, setOpen] = useState(false);
  const notificationsQuery = useNotifications();
  const notifications = notificationsQuery.data ?? [];
  const count = notifications.length;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="relative p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600"
      >
        <Bell className="w-4 h-4" />
        {count > 0 && (
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
        )}
      </button>

      {open && (
        <>
          {/* Overlay para fechar ao clicar fora, sem precisar de lib extra */}
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl border border-gray-200 shadow-lg z-20 max-h-96 overflow-y-auto">
            <div className="px-4 py-3 border-b border-gray-100">
              <span className="text-xs font-bold text-gray-900">Notificações</span>
            </div>
            {notificationsQuery.isLoading && (
              <p className="text-xs text-gray-500 px-4 py-3">Carregando...</p>
            )}
            {count === 0 && !notificationsQuery.isLoading && (
              <p className="text-xs text-gray-500 px-4 py-3">Nenhuma notificação ainda.</p>
            )}
            {notifications.map((notification) => (
              <div key={notification.id} className="px-4 py-3 border-b border-gray-50 last:border-b-0">
                <p className="text-xs text-gray-900">{notification.rendered_body}</p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] font-semibold text-gray-400">
                    {notification.channel}
                  </span>
                  <ElapsedTime createdAt={notification.created_at} />
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
