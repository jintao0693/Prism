/** 按工作空间记住知识库勾选；无记忆时给温和默认。 */

const PREFIX = "prism.kb.selected.";

function storageKey(workspaceId: string): string {
  return `${PREFIX}${workspaceId}`;
}

export function loadKbSelection(workspaceId: string): string[] | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(storageKey(workspaceId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return null;
    return parsed.map(String).filter(Boolean);
  } catch {
    return null;
  }
}

export function saveKbSelection(workspaceId: string, ids: string[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(storageKey(workspaceId), JSON.stringify(ids));
  } catch {
    /* ignore quota / private mode */
  }
}

/** 有记忆用记忆∩现有库；否则 ≤3 全选，否则优先名称含设定/规范/品牌的库，再退回第一个。 */
export function resolveDefaultKbSelection(
  workspaceId: string,
  availableIds: string[],
  namesById?: Record<string, string>,
): string[] {
  if (!availableIds.length) return [];
  const remembered = loadKbSelection(workspaceId);
  if (remembered) {
    const hit = remembered.filter((id) => availableIds.includes(id));
    if (hit.length) return hit;
  }
  if (availableIds.length <= 3) return [...availableIds];
  const preferred = availableIds.filter((id) => {
    const name = namesById?.[id] ?? "";
    return /设定|规范|品牌|视觉|lore|brief/i.test(name);
  });
  if (preferred.length) return preferred.slice(0, 3);
  return [availableIds[0]];
}
