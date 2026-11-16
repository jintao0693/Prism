/**
 * API 客户端。
 * Token：浏览器 localStorage + Cookie（供 RSC 读取）。
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

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

async function resolveAuth(): Promise<{
  token?: string;
  tenantId?: string;
  workspaceId?: string;
}> {
  let token = requestContext.token;
  let tenantId = requestContext.tenantId;
  const workspaceId = requestContext.workspaceId;

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

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  if (USE_MOCK) {
    throw new Error(`Mock mode: use feature APIs instead of apiRequest(${path})`);
  }

  const auth = await resolveAuth();
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

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(text || response.statusText, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
