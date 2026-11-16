import { apiRequest, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import type { KnowledgeBase, KnowledgeHit } from "@/types/domain";

const BASES: KnowledgeBase[] = [
  {
    id: "kb_brand",
    name: "品牌视觉规范",
    description: "VI、主色、禁用示例与历史主视觉。",
    documentCount: 42,
    imageCount: 128,
  },
  {
    id: "kb_ads",
    name: "投放历史素材",
    description: "过往投放图与成片封面，支持图搜复用。",
    documentCount: 6,
    imageCount: 360,
  },
];

const HITS: KnowledgeHit[] = [
  {
    id: "h1",
    title: "spring_hero_v3.png",
    summary: "与查询图构图接近，主色匹配度高。",
    score: 0.91,
    tone: "a",
  },
  {
    id: "h2",
    title: "kv_storefront.jpg",
    summary: "留白比例接近，可作变体参考。",
    score: 0.84,
    tone: "b",
  },
  {
    id: "h3",
    title: "pack_still_02.png",
    summary: "材质光感相近，主体不同。",
    score: 0.76,
    tone: "c",
  },
];

function mapKb(raw: Record<string, unknown>): KnowledgeBase {
  return {
    id: String(raw.id),
    name: String(raw.name),
    description: String(raw.description ?? ""),
    documentCount: Number(raw.documentCount ?? raw.document_count ?? 0),
    imageCount: Number(raw.imageCount ?? raw.image_count ?? 0),
  };
}

function mapHit(raw: Record<string, unknown>): KnowledgeHit {
  const tone = String(raw.tone ?? "a");
  return {
    id: String(raw.id),
    title: String(raw.title),
    summary: String(raw.summary ?? ""),
    score: Number(raw.score ?? 0),
    tone: (tone === "b" || tone === "c" ? tone : "a") as KnowledgeHit["tone"],
  };
}

export async function createKnowledgeBase(
  workspaceId: string,
  name: string,
  description = "",
): Promise<KnowledgeBase> {
  if (USE_MOCK) {
    await mockDelay(200);
    const created: KnowledgeBase = {
      id: `kb_${Date.now()}`,
      name,
      description,
      documentCount: 0,
      imageCount: 0,
    };
    BASES.unshift(created);
    return created;
  }
  const raw = await apiRequest<Record<string, unknown>>(
    "/knowledge-bases",
    {
      method: "POST",
      body: JSON.stringify({ name, description }),
    },
    { workspaceId },
  );
  return mapKb(raw);
}

export async function listKnowledgeBases(
  workspaceId: string,
): Promise<KnowledgeBase[]> {
  if (USE_MOCK) {
    await mockDelay();
    return BASES;
  }
  const raw = await apiRequest<Record<string, unknown>[]>(
    "/knowledge-bases",
    {},
    { workspaceId },
  );
  return raw.map(mapKb);
}

export async function getKnowledgeBase(
  kbId: string,
  workspaceId?: string,
): Promise<KnowledgeBase> {
  if (USE_MOCK) {
    await mockDelay(120);
    const found = BASES.find((b) => b.id === kbId);
    if (!found) throw new Error(`知识库不存在: ${kbId}`);
    return found;
  }
  const raw = await apiRequest<Record<string, unknown>>(
    `/knowledge-bases/${kbId}`,
    {},
    workspaceId ? { workspaceId } : undefined,
  );
  return mapKb(raw);
}

export async function searchByImage(
  kbId: string,
  queryHint?: string,
  workspaceId?: string,
): Promise<KnowledgeHit[]> {
  if (USE_MOCK) {
    void kbId;
    void queryHint;
    await mockDelay(450);
    return HITS;
  }
  const raw = await apiRequest<Record<string, unknown>[]>(
    `/knowledge-bases/${kbId}/search/image`,
    {
      method: "POST",
      body: JSON.stringify({ queryHint: queryHint ?? null }),
    },
    workspaceId ? { workspaceId } : undefined,
  );
  return raw.map(mapHit);
}

export async function searchByText(
  kbId: string,
  query: string,
  workspaceId?: string,
): Promise<KnowledgeHit[]> {
  if (USE_MOCK) {
    await mockDelay(350);
    if (!query.trim()) return HITS;
    return HITS.map((h, i) => ({
      ...h,
      summary: `与「${query}」相关：${h.summary}`,
      score: Math.max(0.55, h.score - i * 0.04),
    }));
  }
  const raw = await apiRequest<Record<string, unknown>[]>(
    `/knowledge-bases/${kbId}/search`,
    {
      method: "POST",
      body: JSON.stringify({ query }),
    },
    workspaceId ? { workspaceId } : undefined,
  );
  return raw.map(mapHit);
}
