import { apiRequest, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import type {
  BrandPack,
  UsageSummary,
  Workspace,
  WorkspaceMember,
} from "@/types/domain";

const WORKSPACES: Workspace[] = [
  {
    id: "ws_spring",
    name: "春季大促 2026",
    description: "主视觉、种草短视频与知识库素材集中在此空间。",
    status: "active",
    conversationCount: 12,
    assetCount: 86,
    updatedAtLabel: "2 小时前",
  },
  {
    id: "ws_brand",
    name: "品牌常青",
    description: "VI 规范、历史主视觉与可复用分镜库。",
    status: "evergreen",
    conversationCount: 5,
    assetCount: 214,
    updatedAtLabel: "昨天",
  },
];

const USAGE: UsageSummary = {
  imagesThisMonth: 0,
  videosThisMonth: 0,
  imagesSoftLimit: 50,
  videosSoftLimit: 10,
};

function mapWorkspace(raw: Record<string, unknown>): Workspace {
  return {
    id: String(raw.id),
    name: String(raw.name),
    description: String(raw.description ?? ""),
    status: (raw.status as Workspace["status"]) ?? "active",
    conversationCount: Number(raw.conversationCount ?? raw.conversation_count ?? 0),
    assetCount: Number(raw.assetCount ?? raw.asset_count ?? 0),
    updatedAtLabel: String(raw.updatedAtLabel ?? raw.updated_at_label ?? ""),
  };
}

export async function listWorkspaces(): Promise<Workspace[]> {
  if (USE_MOCK) {
    await mockDelay();
    return WORKSPACES;
  }
  const raw = await apiRequest<Record<string, unknown>[]>("/workspaces");
  return raw.map(mapWorkspace);
}

export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  if (USE_MOCK) {
    await mockDelay(150);
    const found = WORKSPACES.find((w) => w.id === workspaceId);
    if (!found) throw new Error(`工作空间不存在: ${workspaceId}`);
    return found;
  }
  const raw = await apiRequest<Record<string, unknown>>(
    `/workspaces/${workspaceId}`,
  );
  return mapWorkspace(raw);
}

export async function patchWorkspace(
  workspaceId: string,
  patch: { name?: string; description?: string; status?: Workspace["status"] },
): Promise<Workspace> {
  if (USE_MOCK) {
    await mockDelay(120);
    const ws = WORKSPACES.find((w) => w.id === workspaceId);
    if (!ws) throw new Error("工作空间不存在");
    Object.assign(ws, patch);
    return ws;
  }
  const raw = await apiRequest<Record<string, unknown>>(
    `/workspaces/${workspaceId}`,
    {
      method: "PATCH",
      body: JSON.stringify(patch),
    },
    { workspaceId },
  );
  return mapWorkspace(raw);
}

export async function listWorkspaceMembers(
  workspaceId: string,
): Promise<WorkspaceMember[]> {
  if (USE_MOCK) {
    await mockDelay(100);
    return [
      {
        userId: "u_demo",
        name: "林青",
        email: "linqing@prism.demo",
        role: "owner",
        avatarText: "林",
      },
    ];
  }
  const raw = await apiRequest<Record<string, unknown>[]>(
    `/workspaces/${workspaceId}/members`,
    {},
    { workspaceId },
  );
  return raw.map((row) => ({
    userId: String(row.userId ?? row.user_id ?? ""),
    name: String(row.name ?? ""),
    email: String(row.email ?? ""),
    role: (row.role as WorkspaceMember["role"]) ?? "viewer",
    avatarText: String(row.avatarText ?? row.avatar_text ?? "用"),
  }));
}

function mapBrandPack(raw: Record<string, unknown>): BrandPack {
  return {
    name: String(raw.name ?? ""),
    primaryColor: String(raw.primaryColor ?? raw.primary_color ?? ""),
    accentColor: String(raw.accentColor ?? raw.accent_color ?? ""),
    primaryColorName: String(
      raw.primaryColorName ?? raw.primary_color_name ?? "",
    ),
    accentColorName: String(
      raw.accentColorName ?? raw.accent_color_name ?? "",
    ),
    keywords: Array.isArray(raw.keywords)
      ? raw.keywords.map((x) => String(x))
      : [],
    forbidden: Array.isArray(raw.forbidden)
      ? raw.forbidden.map((x) => String(x))
      : [],
    toneHint: String(raw.toneHint ?? raw.tone_hint ?? ""),
  };
}

export async function getBrandPack(workspaceId: string): Promise<BrandPack> {
  if (USE_MOCK) {
    await mockDelay(80);
    return {
      name: "默认品牌包",
      primaryColor: "#1B1F3B",
      accentColor: "#F0C75E",
      primaryColorName: "深空靛",
      accentColorName: "星辉金",
      keywords: ["安静", "干净留白"],
      forbidden: ["高饱和霓虹紫"],
      toneHint: "气质安静、有召唤感。",
    };
  }
  const raw = await apiRequest<Record<string, unknown>>(
    `/workspaces/${workspaceId}/brand-pack`,
    {},
    { workspaceId },
  );
  return mapBrandPack(raw);
}

export async function saveBrandPack(
  workspaceId: string,
  pack: BrandPack,
): Promise<BrandPack> {
  if (USE_MOCK) {
    await mockDelay(120);
    return pack;
  }
  const raw = await apiRequest<Record<string, unknown>>(
    `/workspaces/${workspaceId}/brand-pack`,
    {
      method: "PUT",
      body: JSON.stringify(pack),
    },
    { workspaceId },
  );
  return mapBrandPack(raw);
}

export async function getUsageSummary(): Promise<UsageSummary> {
  if (USE_MOCK) {
    await mockDelay(100);
    return USAGE;
  }
  const raw = await apiRequest<Record<string, unknown>>("/settings/usage");
  return {
    imagesThisMonth: Number(raw.imagesThisMonth ?? raw.images_this_month ?? 0),
    videosThisMonth: Number(raw.videosThisMonth ?? raw.videos_this_month ?? 0),
    imagesSoftLimit: Number(raw.imagesSoftLimit ?? raw.images_soft_limit ?? 50),
    videosSoftLimit: Number(raw.videosSoftLimit ?? raw.videos_soft_limit ?? 10),
  };
}
