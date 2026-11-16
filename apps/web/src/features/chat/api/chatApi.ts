import {
  ApiError,
  apiFetch,
  apiRequest,
  resolveMediaUrl,
  USE_MOCK,
} from "@/lib/api-client";
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
  /** 增量文本（可多次回调） */
  textDelta?: string;
  /** 累计文本（便于直接渲染） */
  content?: string;
  toolLabel?: string;
  results?: GenerationResult[];
  done?: boolean;
  error?: string;
};

export type SendMessageOptions = {
  workspaceId?: string;
  knowledgeBaseIds?: string[];
  referenceAssetIds?: string[];
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

function mapResult(item: unknown, i: number): GenerationResult {
  const r = item as Record<string, unknown>;
  const tone = String(r.tone ?? "a");
  const kind = String(r.kind ?? "");
  const previewRaw = String(r.previewKind ?? r.preview_kind ?? "");
  const previewKind =
    previewRaw === "video" || previewRaw === "poster" || previewRaw === "image"
      ? previewRaw
      : undefined;
  return {
    id: String(r.id ?? `r_${i}`),
    label: String(r.label ?? "结果"),
    tone: (["a", "b", "c", "d", "e", "f"].includes(tone)
      ? tone
      : "a") as GenerationResult["tone"],
    kind: kind === "video" ? "video" : kind === "image" ? "image" : undefined,
    url: resolveMediaUrl(r.url != null ? String(r.url) : undefined),
    thumbUrl: resolveMediaUrl(
      r.thumbUrl != null
        ? String(r.thumbUrl)
        : r.thumb_url != null
          ? String(r.thumb_url)
          : undefined,
    ),
    mimeType:
      r.mimeType != null
        ? String(r.mimeType)
        : r.mime_type != null
          ? String(r.mime_type)
          : undefined,
    previewKind,
    parentAssetId: r.parentAssetId
      ? String(r.parentAssetId)
      : r.parent_asset_id
        ? String(r.parent_asset_id)
        : undefined,
  };
}

function mapMessage(raw: Record<string, unknown>): ChatMessage {
  const resultsRaw = raw.results;
  let results: GenerationResult[] | undefined;
  if (Array.isArray(resultsRaw)) {
    results = resultsRaw.map((item, i) => mapResult(item, i));
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

type StreamState = {
  intent?: string;
  intentSource?: string;
  content: string;
  toolLabel?: string;
  results: GenerationResult[];
};

function handleSseEvent(
  event: string,
  data: Record<string, unknown>,
  state: StreamState,
  onProgress?: (progress: AgentProgress) => void,
): void {
  if (!onProgress) return;

  if (event === "intent.resolved") {
    state.intent = String(data.intent ?? "");
    state.intentSource = String(data.source ?? "");
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: `已识别意图：${intentLabel(state.intent)}`,
      content: state.content,
      results: state.results,
    });
    return;
  }
  if (event === "context.compacted") {
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: `上下文已压缩（第 ${Number(data.generation ?? 1)} 次），正在继续…`,
      content: state.content,
    });
    return;
  }
  if (event === "context.ready") {
    const turns = Number(data.historyCount ?? 0);
    const hasSummary = Boolean(data.hasSummary);
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: hasSummary
        ? `已载入摘要 + 上文 ${turns} 条…`
        : turns > 0
          ? `已载入上文 ${turns} 条，正在生成…`
          : "无上文，正在生成…",
      content: state.content,
    });
    return;
  }
  if (event === "tool.planned") {
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: `已规划工具：${String(data.tool ?? "chat")}`,
      content: state.content,
    });
    return;
  }
  if (event === "tool.start") {
    const name = String(data.name ?? "tool");
    state.toolLabel = name;
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: `正在执行：${name}`,
      toolLabel: state.toolLabel,
      content: state.content,
      results: state.results,
    });
    return;
  }
  if (event === "media.progress") {
    const status = String(data.status ?? "running");
    const elapsed = Number(data.elapsedSec ?? 0);
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: `视频任务 ${status}${elapsed ? ` · ${elapsed}s` : ""}`,
      toolLabel: state.toolLabel,
      content: state.content,
      results: state.results,
    });
    return;
  }
  if (event === "tool.result") {
    const err = data.error != null ? String(data.error) : "";
    if (err) {
      onProgress({
        intent: state.intent,
        intentSource: state.intentSource,
        status: `工具失败：${String(data.name ?? "tool")}`,
        error: err,
        toolLabel: state.toolLabel,
        content: state.content,
        results: state.results,
      });
      return;
    }
    const url = resolveMediaUrl(data.url != null ? String(data.url) : undefined);
    if (url || data.asset_id) {
      const name = String(data.name ?? "result");
      const kind =
        name.includes("video") || name.includes("视频") ? "video" : "image";
      const card: GenerationResult = {
        id: String(data.asset_id ?? `live_${state.results.length}`),
        label: kind === "video" ? "视频" : "图片",
        tone: "c",
        kind,
        url,
      };
      const withoutDup = state.results.filter((r) => r.id !== card.id);
      state.results = [...withoutDup, card];
    }
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: `工具完成：${String(data.name ?? "tool")}`,
      toolLabel: state.toolLabel,
      content: state.content,
      results: state.results,
    });
    return;
  }
  if (event === "text.delta") {
    const chunk = data.text != null ? String(data.text) : "";
    if (chunk) {
      // 后端目前多为整段替换；若是短增量则追加
      if (!state.content || chunk.startsWith(state.content) || chunk.length > state.content.length + 8) {
        state.content = chunk;
      } else {
        state.content += chunk;
      }
    }
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: state.intent
        ? `正在${intentLabel(state.intent)}回复…`
        : "正在生成回复…",
      textDelta: chunk,
      content: state.content,
      toolLabel: state.toolLabel,
      results: state.results,
    });
    return;
  }
  if (event === "message.done") {
    const content = String(data.content ?? state.content ?? "");
    state.content = content;
    if (data.toolLabel) state.toolLabel = String(data.toolLabel);
    if (Array.isArray(data.results)) {
      state.results = data.results.map((item, i) => mapResult(item, i));
    }
    onProgress({
      intent: state.intent,
      intentSource: state.intentSource,
      status: "完成",
      content: state.content,
      toolLabel: state.toolLabel,
      results: state.results,
      done: true,
    });
  }
}

async function consumeSseStream(
  response: Response,
  onProgress?: (progress: AgentProgress) => void,
): Promise<StreamState> {
  const state: StreamState = { content: "", results: [] };
  const applyBlock = (block: string) => {
    const lines = block.split("\n");
    let event = "message";
    let dataStr = "";
    for (const line of lines) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      if (line.startsWith("data:")) dataStr += line.slice(5).trim();
    }
    if (!dataStr) return;
    let data: Record<string, unknown> = {};
    try {
      data = JSON.parse(dataStr) as Record<string, unknown>;
    } catch {
      return;
    }
    // 兼容 data 内自带 type
    const type = event === "message" && data.type ? String(data.type) : event;
    const payload =
      data.data && typeof data.data === "object"
        ? (data.data as Record<string, unknown>)
        : data;
    handleSseEvent(type, payload, state, onProgress);
  };

  if (!response.body) {
    const text = await response.text();
    for (const block of text.split("\n\n")) {
      if (block.trim()) applyBlock(block);
    }
    return state;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      if (part.trim()) applyBlock(part);
    }
  }
  if (buffer.trim()) applyBlock(buffer);
  return state;
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

/** 发送消息：边收 SSE 边回调；结束后再拉一次消息做权威对齐。 */
export async function sendMessage(
  conversationId: string,
  content: string,
  options?: SendMessageOptions | string,
): Promise<ChatMessage[]> {
  const opts: SendMessageOptions =
    typeof options === "string" ? { workspaceId: options } : options ?? {};
  const { workspaceId, knowledgeBaseIds, referenceAssetIds, onProgress } = opts;

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
    onProgress?.({
      status: "完成",
      content: assistantMsg.content,
      done: true,
    });
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
        referenceAssetIds: referenceAssetIds ?? [],
      }),
    },
    overrides,
  );

  if (!response.ok) {
    const text = await response.text();
    let message = text || `发送失败 (${response.status})`;
    try {
      const parsed = JSON.parse(text) as { detail?: unknown };
      if (typeof parsed.detail === "string") message = parsed.detail;
    } catch {
      // keep raw
    }
    throw new ApiError(message, response.status);
  }

  await consumeSseStream(response, onProgress);
  return getConversationMessages(conversationId, workspaceId);
}
