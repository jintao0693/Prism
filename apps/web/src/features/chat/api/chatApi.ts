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
  {
    id: "c_teaser",
    title: "种草短视频分镜",
    kind: "video",
    updatedAtLabel: "昨天",
    thumbTone: "b",
  },
  {
    id: "c_pack",
    title: "包装静物三视图",
    kind: "image",
    updatedAtLabel: "周一",
    thumbTone: "c",
  },
];

const MESSAGES: Record<string, ChatMessage[]> = {
  c_spring: [
    {
      id: "m1",
      role: "user",
      content:
        "用品牌青石色和暖橙高光，做 3 张春季大促主视觉，横版，干净留白，适合电商首页。",
      createdAt: "2026-03-20T14:18:00+08:00",
    },
    {
      id: "m2",
      role: "assistant",
      content:
        "已结合「品牌常青」知识库中的主色规范，生成 3 个变体。可点选后继续改构图或出短视频。",
      toolLabel: "text_to_image · 完成",
      results: [
        { id: "r1", label: "变体 A", tone: "a" },
        { id: "r2", label: "变体 B", tone: "b" },
        { id: "r3", label: "变体 C", tone: "c" },
      ],
      createdAt: "2026-03-20T14:20:00+08:00",
    },
  ],
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

/** 发送消息：消费后端 SSE，完成后重新拉取完整消息列表。 */
export async function sendMessage(
  conversationId: string,
  content: string,
  workspaceId?: string,
): Promise<ChatMessage[]> {
  if (USE_MOCK) {
    await mockDelay(600);
    const isGenerate = /生成|出图|视频|海报|封面/.test(content);
    const userMsg: ChatMessage = {
      id: `u_${Date.now()}`,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };
    const assistantMsg: ChatMessage = isGenerate
      ? {
          id: `a_${Date.now()}`,
          role: "assistant",
          content: "已根据你的描述完成一轮生成，结果已归档到资产中心（演示数据）。",
          toolLabel: "text_to_image · 完成",
          results: [
            { id: "nr1", label: "新变体 A", tone: "a" },
            { id: "nr2", label: "新变体 B", tone: "b" },
          ],
          createdAt: new Date().toISOString(),
        }
      : {
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

  const overrides = workspaceId ? { workspaceId } : undefined;
  const response = await apiFetch(
    `/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({ content }),
    },
    overrides,
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `发送失败 (${response.status})`);
  }

  // 读完 SSE，确保服务端落库完成后再拉历史
  await response.text();
  return getConversationMessages(conversationId, workspaceId);
}
