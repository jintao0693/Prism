import { apiRequest, resolveMediaUrl, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import type { AssetItem, AssetKind } from "@/types/domain";

const ASSETS: AssetItem[] = [
  {
    id: "a1",
    name: "hero_01.png",
    kind: "image",
    meta: "对话生成 · 今天",
    tone: "a",
  },
  {
    id: "a2",
    name: "hero_02.png",
    kind: "image",
    meta: "对话生成 · 今天",
    tone: "b",
  },
  {
    id: "a3",
    name: "teaser.mp4",
    kind: "video",
    meta: "15s · 图生视频",
    tone: "c",
  },
  {
    id: "a4",
    name: "ref_pack.jpg",
    kind: "image",
    meta: "上传 · 图搜源",
    tone: "d",
  },
  {
    id: "a5",
    name: "story_03.png",
    kind: "image",
    meta: "对话生成 · 昨天",
    tone: "e",
  },
  {
    id: "a6",
    name: "still_set.png",
    kind: "image",
    meta: "对话生成 · 周一",
    tone: "f",
  },
];

function mapAsset(raw: Record<string, unknown>): AssetItem {
  const tone = String(raw.tone ?? "a");
  const kind = String(raw.kind) === "video" ? "video" : "image";
  const previewRaw = String(raw.previewKind ?? raw.preview_kind ?? "");
  const previewKind =
    previewRaw === "video" || previewRaw === "poster" || previewRaw === "image"
      ? previewRaw
      : undefined;
  return {
    id: String(raw.id),
    name: String(raw.name),
    kind,
    meta: String(raw.meta ?? ""),
    tone: tone as AssetItem["tone"],
    url: resolveMediaUrl(raw.url != null ? String(raw.url) : undefined),
    thumbUrl: resolveMediaUrl(
      raw.thumbUrl != null
        ? String(raw.thumbUrl)
        : raw.thumb_url != null
          ? String(raw.thumb_url)
          : undefined,
    ),
    mimeType:
      raw.mimeType != null
        ? String(raw.mimeType)
        : raw.mime_type != null
          ? String(raw.mime_type)
          : undefined,
    previewKind,
  };
}

export async function listAssets(
  workspaceId: string,
  kind: AssetKind | "all" = "all",
): Promise<AssetItem[]> {
  if (USE_MOCK) {
    await mockDelay();
    if (kind === "all") return ASSETS;
    return ASSETS.filter((a) => a.kind === kind);
  }
  const qs = kind === "all" ? "" : `?kind=${encodeURIComponent(kind)}`;
  const raw = await apiRequest<Record<string, unknown>[]>(
    `/assets${qs}`,
    {},
    { workspaceId },
  );
  return raw.map(mapAsset);
}

export async function uploadAsset(
  workspaceId: string,
  file: File,
  options?: { conversationId?: string },
): Promise<AssetItem> {
  if (USE_MOCK) {
    await mockDelay(300);
    const created: AssetItem = {
      id: `a_up_${Date.now()}`,
      name: file.name,
      kind: "image",
      meta: "上传 · 参考图",
      tone: "d",
      url: URL.createObjectURL(file),
    };
    ASSETS.unshift(created);
    return created;
  }
  const form = new FormData();
  form.append("file", file);
  if (options?.conversationId) {
    form.append("conversation_id", options.conversationId);
  }
  const raw = await apiRequest<Record<string, unknown>>(
    "/assets/upload",
    { method: "POST", body: form },
    { workspaceId },
  );
  return mapAsset(raw);
}
