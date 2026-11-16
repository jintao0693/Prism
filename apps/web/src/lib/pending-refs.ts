/** 资产中心 → 对话：待引用参考图（sessionStorage）。 */

export type PendingReferenceAsset = {
  id: string;
  name: string;
  thumbUrl?: string;
  url?: string;
};

const KEY = "prism_pending_reference_assets";

type Payload = {
  workspaceId: string;
  assets: PendingReferenceAsset[];
  ts: number;
};

export function stashPendingReferences(
  workspaceId: string,
  assets: PendingReferenceAsset[],
): void {
  if (typeof window === "undefined" || !assets.length) return;
  const payload: Payload = {
    workspaceId,
    assets: assets.slice(0, 4),
    ts: Date.now(),
  };
  sessionStorage.setItem(KEY, JSON.stringify(payload));
}

export function takePendingReferences(
  workspaceId: string,
): PendingReferenceAsset[] {
  if (typeof window === "undefined") return [];
  const raw = sessionStorage.getItem(KEY);
  if (!raw) return [];
  try {
    const data = JSON.parse(raw) as Payload;
    if (data.workspaceId !== workspaceId) return [];
    sessionStorage.removeItem(KEY);
    return Array.isArray(data.assets) ? data.assets.slice(0, 4) : [];
  } catch {
    sessionStorage.removeItem(KEY);
    return [];
  }
}
