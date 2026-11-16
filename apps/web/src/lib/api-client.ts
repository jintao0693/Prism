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

/** 尽量抽出 FastAPI `detail` 文案，避免把整段 JSON 丢给用户。 */
function formatApiError(text: string, fallback: string): string {
  const raw = (text || "").trim();
  if (!raw) return fallback || "请求失败";
  try {
    const parsed = JSON.parse(raw) as { detail?: unknown };
    const detail = parsed.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: unknown }).msg);
          }
          return JSON.stringify(item);
        })
        .filter(Boolean)
        .join("；");
    }
  } catch {
    // 非 JSON 时原样返回
  }
  return raw.length > 280 ? `${raw.slice(0, 280)}…` : raw;
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

/** 将后端 `/media/...` 相对路径拼成浏览器可访问的绝对 URL。 */
export function resolveMediaUrl(path?: string | null): string | undefined {
  if (!path) return undefined;
  if (
    path.startsWith("http://") ||
    path.startsWith("https://") ||
    path.startsWith("data:") ||
    path.startsWith("blob:")
  ) {
    return path;
  }
  const origin = resolveApiBase().replace(/\/api\/v1\/?$/, "");
  return `${origin}${path.startsWith("/") ? path : `/${path}`}`;
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
  const isFormData =
    typeof FormData !== "undefined" && init.body instanceof FormData;
  // FormData 需由浏览器自带 multipart boundary，不可强制 JSON
  if (!headers.has("Content-Type") && init.body && !isFormData) {
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
    throw new ApiError(formatApiError(text, response.statusText), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
