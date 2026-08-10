/**
 * Cliente HTTP fino compartilhado pelos módulos de API do cardápio digital
 * (app público, sem autenticação — o escopo de tenant vem do header
 * `X-Tenant-Id`, resolvido a partir do slug na URL).
 *
 * Traduz respostas de erro no formato RFC 7807 Problem Details
 * (`restaurant_common.problem_details` no backend) em `ApiError`.
 */

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

interface ProblemDetails {
  title?: string;
  detail?: string;
  code?: string;
}

export interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  tenantId?: string;
  /** Header `Idempotency-Key` — evita duplicar um pagamento em retry de
   * rede/reconexão (o `payment-service` já suporta, ver docs/SECURITY.md). */
  idempotencyKey?: string;
}

export async function apiRequest<TResponse>(
  baseUrl: string,
  path: string,
  options: RequestOptions = {},
): Promise<TResponse> {
  const { method = 'GET', body, tenantId, idempotencyKey } = options;

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (tenantId) {
    headers['X-Tenant-Id'] = tenantId;
  }
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }

  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    let problem: ProblemDetails = {};
    try {
      problem = (await response.json()) as ProblemDetails;
    } catch {
      // corpo não era JSON — segue com a mensagem genérica.
    }
    throw new ApiError(
      problem.detail ?? problem.title ?? `Falha na requisição (HTTP ${response.status}).`,
      response.status,
      problem.code,
    );
  }

  return (await response.json()) as TResponse;
}
