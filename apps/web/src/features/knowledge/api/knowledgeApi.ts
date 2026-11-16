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

export async function listKnowledgeBases(
  workspaceId: string,
): Promise<KnowledgeBase[]> {
  void workspaceId;
  await mockDelay();
  return BASES;
}

export async function getKnowledgeBase(kbId: string): Promise<KnowledgeBase> {
  await mockDelay(120);
  const found = BASES.find((b) => b.id === kbId);
  if (!found) {
    throw new Error(`知识库不存在: ${kbId}`);
  }
  return found;
}

export async function searchByImage(
  kbId: string,
  queryHint?: string,
): Promise<KnowledgeHit[]> {
  void kbId;
  void queryHint;
  await mockDelay(450);
  return HITS;
}

export async function searchByText(
  kbId: string,
  query: string,
): Promise<KnowledgeHit[]> {
  void kbId;
  await mockDelay(350);
  if (!query.trim()) {
    return HITS;
  }
  return HITS.map((h, i) => ({
    ...h,
    summary: `与「${query}」相关：${h.summary}`,
    score: Math.max(0.55, h.score - i * 0.04),
  }));
}
