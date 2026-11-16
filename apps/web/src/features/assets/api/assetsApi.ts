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

const MODE_LABELS: Record<string, string> = {
  text_to_image: "文生图",
  image_to_image: "图生图",
  text_to_video: "文生视频",
  image_to_video: "图生视频",
  upload: "上传",
};

function providerLabel(provider: string): string {
  if (!provider) return "";
  if (provider.includes("volc") || provider.includes("ark")) return "火山方舟";
  if (provider.includes("demo")) return "演示";
  return provider;
}

/** 把后端 JSON meta 收成一行可读文案（工作台 / 资产中心共用）。 */
export function formatAssetMetaLabel(
  rawMeta: unknown,
  kind: AssetKind = "image",
): string {
  const text = rawMeta == null ? "" : String(rawMeta).trim();
  if (!text) return kind === "video" ? "视频资产" : "图片资产";
  if (!text.startsWith("{")) return text;

  try {
    const data = JSON.parse(text) as Record<string, unknown>;
    const mode = String(data.mode ?? "");
    const modeLabel =
      MODE_LABELS[mode] ||
      (kind === "video" ? "视频" : mode ? mode : "图片");
    const prompt = String(data.prompt ?? "").replace(/\s+/g, " ").trim();
    const snippet =
      prompt.length > 28 ? `${prompt.slice(0, 28)}…` : prompt;
    const provider = providerLabel(String(data.provider ?? ""));
    const parts = [modeLabel];
    if (snippet) parts.push(snippet);
    else if (provider) parts.push(provider);
    return parts.join(" · ");
  } catch {
    return text.length > 48 ? `${text.slice(0, 48)}…` : text;
  }
}

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
    meta: formatAssetMetaLabel(raw.meta, kind),
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
    parentAssetId:
      raw.parentAssetId != null
        ? String(raw.parentAssetId)
        : raw.parent_asset_id != null
          ? String(raw.parent_asset_id)
          : undefined,
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
