import { apiFetch, apiRequest, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import type { ChatMessage, ConversationSummary, GenerationResult } from "@/types/domain";

const CONVERSATIONS: ConversationSummary[] = [
  {
    id: "c_spring",
    title: "春季主视觉 · 青橙光谱",
    kind: "image",
    updatedAtLabel: "今天 14:20",
    thumbTone: "a",
  },
];

const MESSAGES: Record<string, ChatMessage[]> = {};

export type AgentProgress = {
  intent?: string;
  intentSource?: string;
  status: string;
};

export type SendMessageOptions = {
  workspaceId?: string;
  knowledgeBaseIds?: string[];
  onProgress?: (progress: AgentProgress) => void;
};

function mapConversation(raw: Record<string, unknown>): ConversationSummary {
  const kind = String(raw.kind ?? "chat");
  return {
    id: String(raw.id),
    title: String(raw.title),
    kind: (kind === "image" || kind === "video" || kind === "chat"
      ? kind
      : "chat") as ConversationSummary["kind"],
    updatedAtLabel: String(raw.updatedAtLabel ?? raw.updated_at_label ?? ""),
    thumbTone: (String(raw.thumbTone ?? raw.thumb_tone ?? "a") ||
      "a") as ConversationSummary["thumbTone"],
  };
}

function mapMessage(raw: Record<string, unknown>): ChatMessage {
  const resultsRaw = raw.results;
  let results: GenerationResult[] | undefined;
  if (Array.isArray(resultsRaw)) {
    results = resultsRaw.map((item, i) => {
      const r = item as Record<string, unknown>;
      const tone = String(r.tone ?? "a");
      return {
        id: String(r.id ?? `r_${i}`),
        label: String(r.label ?? "结果"),
        tone: (tone === "b" || tone === "c" ? tone : "a") as GenerationResult["tone"],
      };
    });
  }
  return {
    id: String(raw.id),
    role: raw.role === "user" ? "user" : "assistant",
    content: String(raw.content ?? ""),
    toolLabel: raw.toolLabel
      ? String(raw.toolLabel)
      : raw.tool_label
        ? String(raw.tool_label)
        : undefined,
    results,
    createdAt: String(raw.createdAt ?? raw.created_at ?? new Date().toISOString()),
  };
}

function intentLabel(intent?: string): string {
  switch (intent) {
    case "image":
      return "生图";
    case "video":
      return "生视频";
    case "knowledge":
      return "知识库问答";
    case "chat":
      return "文本问答";
    default:
      return intent ?? "处理中";
  }
}

function consumeSseProgress(
  raw: string,
  onProgress?: (progress: AgentProgress) => void,
): void {
  if (!onProgress) return;
  let intent: string | undefined;
  let intentSource: string | undefined;
  const blocks = raw.split("\n\n");
  for (const block of blocks) {
    const lines = block.split("\n");
    let event = "message";
    let dataStr = "";
    for (const line of lines) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      if (line.startsWith("data:")) dataStr += line.slice(5).trim();
    }
    if (!dataStr) continue;
    let data: Record<string, unknown> = {};
    try {
      data = JSON.parse(dataStr) as Record<string, unknown>;
    } catch {
      continue;
    }
    if (event === "intent.resolved") {
      intent = String(data.intent ?? "");
      intentSource = String(data.source ?? "");
      onProgress({
        intent,
        intentSource,
        status: `已识别意图：${intentLabel(intent)}`,
      });
    } else if (event === "tool.start") {
      const name = String(data.name ?? "tool");
      onProgress({
        intent,
        intentSource,
        status: `正在执行：${name}`,
      });
    } else if (event === "tool.result") {
      onProgress({
        intent,
        intentSource,
        status: `工具完成：${String(data.name ?? "tool")}`,
      });
    } else if (event === "text.delta" && data.text) {
      onProgress({
        intent,
        intentSource,
        status: intent ? `正在${intentLabel(intent)}回复…` : "正在生成回复…",
      });
    }
  }
}

export async function listConversations(
  workspaceId: string,
): Promise<ConversationSummary[]> {
  if (USE_MOCK) {
    await mockDelay();
    return CONVERSATIONS;
  }
  const raw = await apiRequest<Record<string, unknown>[]>(
    "/conversations",
    {},
    { workspaceId },
  );
  return raw.map(mapConversation);
}

export async function createConversation(
  workspaceId: string,
  title = "新对话",
  kind: ConversationSummary["kind"] = "chat",
): Promise<ConversationSummary> {
  if (USE_MOCK) {
    await mockDelay(200);
    const created: ConversationSummary = {
      id: `c_${Date.now()}`,
      title,
      kind,
      updatedAtLabel: "刚刚",
      thumbTone: "a",
    };
    CONVERSATIONS.unshift(created);
    return created;
  }
  const raw = await apiRequest<Record<string, unknown>>(
    "/conversations",
    {
      method: "POST",
      body: JSON.stringify({ title, kind }),
    },
    { workspaceId },
  );
  return mapConversation(raw);
}

export async function getConversationMessages(
  conversationId: string,
  workspaceId?: string,
): Promise<ChatMessage[]> {
  if (USE_MOCK) {
    await mockDelay(200);
    return MESSAGES[conversationId] ?? [];
  }
  const raw = await apiRequest<Record<string, unknown>[]>(
    `/conversations/${conversationId}/messages`,
    {},
    workspaceId ? { workspaceId } : undefined,
  );
  return raw.map(mapMessage);
}

/** 发送消息：解析 SSE 进度，完成后重新拉取完整消息列表。 */
export async function sendMessage(
  conversationId: string,
  content: string,
  options?: SendMessageOptions | string,
): Promise<ChatMessage[]> {
  // 兼容旧签名 sendMessage(id, text, workspaceId)
  const opts: SendMessageOptions =
    typeof options === "string" ? { workspaceId: options } : options ?? {};
  const { workspaceId, knowledgeBaseIds, onProgress } = opts;

  if (USE_MOCK) {
    await mockDelay(600);
    onProgress?.({ intent: "chat", intentSource: "mock", status: "演示回复中…" });
    const userMsg: ChatMessage = {
      id: `u_${Date.now()}`,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };
    const assistantMsg: ChatMessage = {
      id: `a_${Date.now()}`,
      role: "assistant",
      content: `这是演示文本回复：已收到「${content.slice(0, 40)}」。`,
      createdAt: new Date().toISOString(),
    };
    const prev = MESSAGES[conversationId] ?? [];
    const next = [...prev, userMsg, assistantMsg];
    MESSAGES[conversationId] = next;
    return next;
  }

  onProgress?.({ status: "正在理解意图…" });
  const overrides = workspaceId ? { workspaceId } : undefined;
  const response = await apiFetch(
    `/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({
        content,
        knowledgeBaseIds: knowledgeBaseIds ?? [],
      }),
    },
    overrides,
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `发送失败 (${response.status})`);
  }

  const sseText = await response.text();
  consumeSseProgress(sseText, onProgress);
  return getConversationMessages(conversationId, workspaceId);
}
