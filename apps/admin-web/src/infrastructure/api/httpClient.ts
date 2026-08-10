/**
 * Cliente HTTP fino compartilhado por todos os módulos de API.
 *
 * Anexa o `Bearer` token da sessão automaticamente e traduz respostas de
 * erro no formato RFC 7807 Problem Details (`restaurant_common.problem_details`
 * no backend) em `ApiError`, para que a UI exiba a mensagem real do backend
 * em vez de um erro HTTP genérico.
 */
import { useSessionStore } from '../state/sessionStore';

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
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  body?: unknown;
  /** Requisição pública — não anexa `Authorization` mesmo se houver sessão. */
  skipAuth?: boolean;
  headers?: Record<string, string>;
}

export async function apiRequest<TResponse>(
  baseUrl: string,
  path: string,
  options: RequestOptions = {},
): Promise<TResponse> {
  const { method = 'GET', body, skipAuth = false, headers = {} } = options;

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  if (!skipAuth) {
    const { accessToken } = useSessionStore.getState();
    if (accessToken) {
      requestHeaders.Authorization = `Bearer ${accessToken}`;
    }
  }

  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: requestHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    let problem: ProblemDetails = {};
    try {
      problem = (await response.json()) as ProblemDetails;
    } catch {
      // corpo não era JSON (ex: 502 de um proxy) — segue com a mensagem genérica.
    }
    throw new ApiError(
      problem.detail ?? problem.title ?? `Falha na requisição (HTTP ${response.status}).`,
      response.status,
      problem.code,
    );
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}
