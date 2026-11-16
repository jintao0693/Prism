import {
  apiRequest,
  resolveMediaUrl,
  USE_MOCK,
} from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import type {
  KnowledgeBase,
  KnowledgeHit,
  KnowledgeItem,
} from "@/types/domain";

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
    itemType: "image",
  },
  {
    id: "h2",
    title: "kv_storefront.jpg",
    summary: "留白比例接近，可作变体参考。",
    score: 0.84,
    tone: "b",
    itemType: "image",
  },
  {
    id: "h3",
    title: "pack_still_02.png",
    summary: "材质光感相近，主体不同。",
    score: 0.76,
    tone: "c",
    itemType: "image",
  },
];

const TONES = ["a", "b", "c", "d", "e", "f"] as const;

function mapTone(raw: unknown): KnowledgeHit["tone"] {
  const tone = String(raw ?? "a");
  return (TONES.includes(tone as (typeof TONES)[number])
    ? tone
    : "a") as KnowledgeHit["tone"];
}

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
  const itemTypeRaw = String(raw.itemType ?? raw.item_type ?? "image");
  return {
    id: String(raw.id),
    title: String(raw.title),
    summary: String(raw.summary ?? ""),
    score: Number(raw.score ?? 0),
    tone: mapTone(raw.tone),
    itemType: itemTypeRaw === "document" ? "document" : "image",
    url: resolveMediaUrl(
      raw.url != null ? String(raw.url) : undefined,
    ),
  };
}

function mapItem(raw: Record<string, unknown>): KnowledgeItem {
  const itemTypeRaw = String(raw.itemType ?? raw.item_type ?? "document");
  return {
    id: String(raw.id),
    title: String(raw.title),
    itemType: itemTypeRaw === "image" ? "image" : "document",
    summary: String(raw.summary ?? ""),
    url: resolveMediaUrl(
      raw.url != null ? String(raw.url) : undefined,
    ),
    hasEmbedding: Boolean(raw.hasEmbedding ?? raw.has_embedding),
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

export async function listKnowledgeItems(
  kbId: string,
  workspaceId: string,
): Promise<KnowledgeItem[]> {
  if (USE_MOCK) {
    await mockDelay(150);
    return HITS.map((h) => ({
      id: h.id,
      title: h.title,
      itemType: "image" as const,
      summary: h.summary,
      hasEmbedding: true,
    }));
  }
  const raw = await apiRequest<Record<string, unknown>[]>(
    `/knowledge-bases/${kbId}/items`,
    {},
    { workspaceId },
  );
  return raw.map(mapItem);
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

/** 真·以图搜图：上传参考图。 */
export async function searchByImageFile(
  kbId: string,
  file: File,
  workspaceId: string,
  queryHint?: string,
): Promise<KnowledgeHit[]> {
  if (USE_MOCK) {
    await mockDelay(500);
    return HITS.map((h) => ({
      ...h,
      summary: `与「${file.name}」相似：${h.summary}`,
    }));
  }
  const form = new FormData();
  form.append("file", file);
  if (queryHint?.trim()) form.append("query_hint", queryHint.trim());
  form.append("top_k", "8");
  const raw = await apiRequest<Record<string, unknown>[]>(
    `/knowledge-bases/${kbId}/search/by-image`,
    { method: "POST", body: form },
    { workspaceId },
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

export async function ingestDocument(
  kbId: string,
  workspaceId: string,
  title: string,
  content: string,
): Promise<{ id: string; hasEmbedding: boolean }> {
  if (USE_MOCK) {
    await mockDelay(250);
    return { id: `ki_mock_${Date.now()}`, hasEmbedding: false };
  }
  const raw = await apiRequest<Record<string, unknown>>(
    `/knowledge-bases/${kbId}/documents`,
    {
      method: "POST",
      body: JSON.stringify({ title, content }),
    },
    { workspaceId },
  );
  return {
    id: String(raw.id),
    hasEmbedding: Boolean(raw.hasEmbedding ?? raw.has_embedding),
  };
}

export async function ingestImage(
  kbId: string,
  workspaceId: string,
  file: File,
  opts?: { title?: string; caption?: string },
): Promise<KnowledgeItem> {
  if (USE_MOCK) {
    await mockDelay(400);
    return {
      id: `ki_mock_${Date.now()}`,
      title: opts?.title || file.name,
      itemType: "image",
      summary: opts?.caption || file.name,
      hasEmbedding: true,
    };
  }
  const form = new FormData();
  form.append("file", file);
  if (opts?.title) form.append("title", opts.title);
  if (opts?.caption) form.append("caption", opts.caption);
  const raw = await apiRequest<Record<string, unknown>>(
    `/knowledge-bases/${kbId}/images`,
    { method: "POST", body: form },
    { workspaceId },
  );
  return mapItem(raw);
}

export async function reembedItem(
  kbId: string,
  itemId: string,
  workspaceId: string,
): Promise<KnowledgeItem> {
  if (USE_MOCK) {
    await mockDelay(300);
    return {
      id: itemId,
      title: itemId,
      itemType: "image",
      summary: "",
      hasEmbedding: true,
    };
  }
  const raw = await apiRequest<Record<string, unknown>>(
    `/knowledge-bases/${kbId}/items/${itemId}/reembed`,
    { method: "POST" },
    { workspaceId },
  );
  return mapItem(raw);
}

export async function reembedMissing(
  kbId: string,
  workspaceId: string,
): Promise<{ attempted: number; ok: number; failed: { id: string; error: string }[] }> {
  if (USE_MOCK) {
    await mockDelay(400);
    return { attempted: 0, ok: 0, failed: [] };
  }
  return apiRequest(
    `/knowledge-bases/${kbId}/reembed-missing`,
    { method: "POST" },
    { workspaceId },
  );
}

/** 有限并发执行任务，并回调进度。 */
export async function mapWithConcurrency<T, R>(
  items: T[],
  concurrency: number,
  worker: (item: T, index: number) => Promise<R>,
  onProgress?: (done: number, total: number, item: T) => void,
): Promise<R[]> {
  const total = items.length;
  const results = new Array<R>(total);
  let next = 0;
  let done = 0;

  async function runOne(): Promise<void> {
    while (next < total) {
      const index = next;
      next += 1;
      const item = items[index];
      results[index] = await worker(item, index);
      done += 1;
      onProgress?.(done, total, item);
    }
  }

  const runners = Array.from(
    { length: Math.min(Math.max(1, concurrency), Math.max(1, total)) },
    () => runOne(),
  );
  await Promise.all(runners);
  return results;
}
