/** 知识库 / 失败重试：待填入输入框的草稿。 */

const KEY = "prism_pending_composer_draft";

type Payload = {
  workspaceId: string;
  text: string;
  ts: number;
};

export function stashComposerDraft(workspaceId: string, text: string): void {
  if (typeof window === "undefined" || !text.trim()) return;
  const payload: Payload = {
    workspaceId,
    text: text.trim(),
    ts: Date.now(),
  };
  sessionStorage.setItem(KEY, JSON.stringify(payload));
}

export function takeComposerDraft(workspaceId: string): string | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(KEY);
  if (!raw) return null;
  try {
    const data = JSON.parse(raw) as Payload;
    if (data.workspaceId !== workspaceId) return null;
    sessionStorage.removeItem(KEY);
    return data.text || null;
  } catch {
    sessionStorage.removeItem(KEY);
    return null;
  }
}
