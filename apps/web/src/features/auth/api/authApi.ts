import { apiRequest, setRequestContext, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import type { Tenant, User } from "@/types/domain";

const DEMO_USER: User = {
  id: "u_1",
  name: "林清",
  email: "linqing@prism.demo",
  avatarText: "林",
  role: "owner",
};

const DEMO_TENANT: Tenant = {
  id: "t_1",
  name: "品牌星云",
};

const TOKEN_KEY = "prism_access_token";
const TENANT_KEY = "prism_tenant_id";

export function loadStoredAuth(): void {
  if (typeof window === "undefined") return;
  const token = localStorage.getItem(TOKEN_KEY) ?? undefined;
  const tenantId = localStorage.getItem(TENANT_KEY) ?? undefined;
  setRequestContext({ token, tenantId });
}

export function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TENANT_KEY);
  document.cookie = `${TOKEN_KEY}=; path=/; Max-Age=0`;
  document.cookie = `${TENANT_KEY}=; path=/; Max-Age=0`;
  setRequestContext({ token: undefined, tenantId: undefined, workspaceId: undefined });
}

export async function getCurrentUser(): Promise<User> {
  if (USE_MOCK) {
    await mockDelay();
    return DEMO_USER;
  }
  loadStoredAuth();
  const raw = await apiRequest<Record<string, unknown>>("/auth/me");
  return {
    id: String(raw.id),
    name: String(raw.name),
    email: String(raw.email),
    avatarText: String(raw.avatarText ?? raw.avatar_text ?? "用"),
    role: String(raw.role) as User["role"],
  };
}

export async function getCurrentTenant(): Promise<Tenant> {
  if (USE_MOCK) {
    await mockDelay(120);
    return DEMO_TENANT;
  }
  // 登录响应已含租户；此处用本地缓存兜底
  const id = typeof window !== "undefined" ? localStorage.getItem(TENANT_KEY) : null;
  return { id: id ?? "t_1", name: "当前租户" };
}

export async function loginDemo(): Promise<{ user: User; tenant: Tenant }> {
  return loginWithPassword("linqing@prism.demo", "prism123");
}

export async function loginWithPassword(
  email: string,
  password: string,
): Promise<{ user: User; tenant: Tenant; accessToken?: string }> {
  if (USE_MOCK) {
    await mockDelay(400);
    return { user: DEMO_USER, tenant: DEMO_TENANT };
  }

  const raw = await apiRequest<{
    access_token: string;
    user: Record<string, unknown>;
    tenant: { id: string; name: string };
  }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, raw.access_token);
    localStorage.setItem(TENANT_KEY, raw.tenant.id);
    // Cookie 供服务端组件读取
    document.cookie = `${TOKEN_KEY}=${encodeURIComponent(raw.access_token)}; path=/; SameSite=Lax`;
    document.cookie = `${TENANT_KEY}=${encodeURIComponent(raw.tenant.id)}; path=/; SameSite=Lax`;
  }
  setRequestContext({ token: raw.access_token, tenantId: raw.tenant.id });

  return {
    accessToken: raw.access_token,
    user: {
      id: String(raw.user.id),
      name: String(raw.user.name),
      email: String(raw.user.email),
      avatarText: String(raw.user.avatarText ?? "用"),
      role: String(raw.user.role) as User["role"],
    },
    tenant: raw.tenant,
  };
}
