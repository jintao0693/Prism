import { apiRequest, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import { routes } from "@/lib/routes";
import type { ShareLinkResult } from "@/types/domain";

export type PublicShare = {
  title: string;
  note: string;
  resourceType: string;
  resourceId: string;
  url?: string;
  thumbUrl?: string;
  mimeType?: string;
  previewKind?: "image" | "video" | "poster";
  kind?: string;
};

function mapShare(raw: Record<string, unknown>): ShareLinkResult {
  return {
    id: String(raw.id ?? ""),
    token: String(raw.token ?? ""),
    title: String(raw.title ?? ""),
    resourceType: String(raw.resourceType ?? raw.resource_type ?? "asset"),
    resourceId: String(raw.resourceId ?? raw.resource_id ?? ""),
    sharePath: String(raw.sharePath ?? raw.share_path ?? ""),
  };
}

export async function createAssetShare(
  workspaceId: string,
  assetId: string,
  opts?: { title?: string; note?: string },
): Promise<ShareLinkResult> {
  if (USE_MOCK) {
    await mockDelay(150);
    const token = `mock_${assetId.slice(-6)}`;
    return {
      id: "sh_mock",
      token,
      title: opts?.title ?? "资产分享",
      resourceType: "asset",
      resourceId: assetId,
      sharePath: routes.share(token),
    };
  }
  const raw = await apiRequest<Record<string, unknown>>(
    "/shares",
    {
      method: "POST",
      body: JSON.stringify({
        resourceType: "asset",
        resourceId: assetId,
        title: opts?.title,
        note: opts?.note,
      }),
    },
    { workspaceId },
  );
  return mapShare(raw);
}

export async function getPublicShare(token: string): Promise<PublicShare> {
  if (USE_MOCK) {
    await mockDelay(100);
    return {
      title: "演示分享",
      note: "",
      resourceType: "asset",
      resourceId: "asset_mock",
    };
  }
  const raw = await apiRequest<Record<string, unknown>>(`/shares/public/${token}`);
  return {
    title: String(raw.title ?? ""),
    note: String(raw.note ?? ""),
    resourceType: String(raw.resourceType ?? raw.resource_type ?? ""),
    resourceId: String(raw.resourceId ?? raw.resource_id ?? ""),
    url: raw.url != null ? String(raw.url) : undefined,
    thumbUrl:
      raw.thumbUrl != null
        ? String(raw.thumbUrl)
        : raw.thumb_url != null
          ? String(raw.thumb_url)
          : undefined,
    mimeType:
      raw.mimeType != null
        ? String(raw.mimeType)
        : raw.mime_type != null
          ? String(raw.mime_type)
          : undefined,
    previewKind:
      raw.previewKind === "video" ||
      raw.previewKind === "poster" ||
      raw.previewKind === "image"
        ? raw.previewKind
        : undefined,
    kind: raw.kind != null ? String(raw.kind) : undefined,
  };
}