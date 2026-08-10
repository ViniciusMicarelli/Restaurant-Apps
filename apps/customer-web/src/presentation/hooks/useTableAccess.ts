import { useQuery } from '@tanstack/react-query';
import { validateTableQrSecret } from '../../infrastructure/api/diningApi';
import { resolveTableNumber, resolveTableSecret } from '../../infrastructure/restaurantSlug';

export type TableAccessStatus = 'checking' | 'granted' | 'denied';

/**
 * Gate obrigatório do cardápio digital: sem uma secret de mesa válida (QR
 * Code rotativo, ver `admin-web` → Mesas → "Ver QR Code"), o cardápio não
 * carrega — substitui o link estático `?r=slug&table=N` de antes. Valida uma
 * única vez no carregamento da página, não a cada request de menu/pedido.
 */
export function useTableAccess(tenantId: string | undefined): {
  tableNumber: number | null;
  /** Secret de QR Code da mesa, já validada — usada pelo autoatendimento do
   * cliente (US-05.4) pra consultar/fechar a própria comanda e pagar sem JWT. */
  secret: string | null;
  status: TableAccessStatus;
} {
  const tableNumber = resolveTableNumber();
  const secret = resolveTableSecret();
  const hasParams = Boolean(tableNumber && secret);

  const query = useQuery({
    queryKey: ['table-access', tenantId, tableNumber, secret],
    queryFn: () => validateTableQrSecret(tenantId!, tableNumber!, secret!),
    enabled: Boolean(tenantId) && hasParams,
    retry: false,
  });

  let status: TableAccessStatus = 'checking';
  if (!hasParams && tenantId) {
    status = 'denied';
  } else if (query.isSuccess && query.data.valid) {
    status = 'granted';
  } else if (query.isError) {
    status = 'denied';
  }

  return { tableNumber, secret, status };
}
