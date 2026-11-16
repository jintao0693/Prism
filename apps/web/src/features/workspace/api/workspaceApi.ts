import { apiRequest, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import type { UsageSummary, Workspace } from "@/types/domain";

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
  imagesThisMonth: 128,
  videosThisMonth: 14,
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

export async function getUsageSummary(): Promise<UsageSummary> {
  if (USE_MOCK) {
    await mockDelay(100);
    return USAGE;
  }
  const raw = await apiRequest<Record<string, unknown>>("/settings/usage");
  return {
    imagesThisMonth: Number(raw.imagesThisMonth ?? raw.images_this_month ?? 0),
    videosThisMonth: Number(raw.videosThisMonth ?? raw.videos_this_month ?? 0),
  };
}
