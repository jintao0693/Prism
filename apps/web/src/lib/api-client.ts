/**
 * API 客户端。
 * Token：浏览器 localStorage + Cookie（供 RSC 读取）。
 *
 * 服务端（RSC）优先读 API_BASE_URL（Docker 内可指向 http://api:8000/...），
 * 浏览器读 NEXT_PUBLIC_API_BASE_URL（指向宿主机可访问地址）。
 */

function resolveApiBase(): string {
  const fallback = "http://127.0.0.1:8000/api/v1";
  if (typeof window === "undefined") {
    return (
      process.env.API_BASE_URL ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      fallback
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? fallback;
}

/** 仅当显式设为 true 时走前端 mock，默认接真实后端。 */
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface RequestContext {
  tenantId?: string;
  workspaceId?: string;
  token?: string;
}

let requestContext: RequestContext = {};

export function setRequestContext(ctx: RequestContext): void {
  requestContext = { ...requestContext, ...ctx };
}

export function getRequestContext(): RequestContext {
  return requestContext;
}

export function getApiBaseUrl(): string {
  return resolveApiBase();
}

async function resolveAuth(
  overrides?: RequestContext,
): Promise<{
  token?: string;
  tenantId?: string;
  workspaceId?: string;
}> {
  let token = overrides?.token ?? requestContext.token;
  let tenantId = overrides?.tenantId ?? requestContext.tenantId;
  const workspaceId = overrides?.workspaceId ?? requestContext.workspaceId;

  if (typeof window !== "undefined") {
    token = token ?? localStorage.getItem("prism_access_token") ?? undefined;
    tenantId = tenantId ?? localStorage.getItem("prism_tenant_id") ?? undefined;
  } else {
    try {
      const { cookies } = await import("next/headers");
      const jar = await cookies();
      token = token ?? jar.get("prism_access_token")?.value;
      tenantId = tenantId ?? jar.get("prism_tenant_id")?.value;
    } catch {
      // 非 Next 请求上下文时忽略
    }
  }

  return { token, tenantId, workspaceId };
}

async function buildHeaders(
  init: RequestInit,
  overrides?: RequestContext,
): Promise<Headers> {
  const auth = await resolveAuth(overrides);
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (auth.token) {
    headers.set("Authorization", `Bearer ${auth.token}`);
  }
  if (auth.tenantId) {
    headers.set("X-Tenant-Id", auth.tenantId);
  }
  if (auth.workspaceId) {
    headers.set("X-Workspace-Id", auth.workspaceId);
  }
  return headers;
}

/** 底层 fetch（含鉴权头），用于 SSE 等非 JSON 响应。 */
export async function apiFetch(
  path: string,
  init: RequestInit = {},
  overrides?: RequestContext,
): Promise<Response> {
  if (USE_MOCK) {
    throw new Error(`Mock mode: use feature APIs instead of apiFetch(${path})`);
  }
  const headers = await buildHeaders(init, overrides);
  return fetch(`${resolveApiBase()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  overrides?: RequestContext,
): Promise<T> {
  if (USE_MOCK) {
    throw new Error(`Mock mode: use feature APIs instead of apiRequest(${path})`);
  }

  const response = await apiFetch(path, init, overrides);

  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(text || response.statusText, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
