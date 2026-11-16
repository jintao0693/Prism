import { mockDelay } from "@/lib/mock-delay";
import type { ChatMessage, ConversationSummary } from "@/types/domain";

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
  c_teaser: [
    {
      id: "m3",
      role: "user",
      content: "根据这张主视觉做一条 15 秒种草短视频，竖屏。",
      createdAt: "2026-03-19T10:00:00+08:00",
    },
    {
      id: "m4",
      role: "assistant",
      content: "已规划三镜分镜并提交图生视频任务。成片就绪后会进入资产中心。",
      toolLabel: "image_to_video · 完成",
      createdAt: "2026-03-19T10:08:00+08:00",
    },
  ],
  c_pack: [
    {
      id: "m5",
      role: "user",
      content: "我们包装主色规范是什么？",
      createdAt: "2026-03-17T09:00:00+08:00",
    },
    {
      id: "m6",
      role: "assistant",
      content:
        "根据知识库「品牌视觉规范」：主色为青石色 #0F6E6A，点缀暖橙 #E8A838，背景保持冷雾白留白，避免使用高饱和紫色。",
      createdAt: "2026-03-17T09:00:12+08:00",
    },
  ],
};

export async function listConversations(
  workspaceId: string,
): Promise<ConversationSummary[]> {
  void workspaceId;
  await mockDelay();
  return CONVERSATIONS;
}

export async function getConversationMessages(
  conversationId: string,
): Promise<ChatMessage[]> {
  await mockDelay(200);
  return MESSAGES[conversationId] ?? [];
}

export async function sendMessage(
  conversationId: string,
  content: string,
): Promise<ChatMessage[]> {
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
        content: `这是演示文本回复：已收到「${content.slice(0, 40)}」。后端接入 Pydantic AI Harness 后，将在此流式输出真实答案。`,
        createdAt: new Date().toISOString(),
      };

  const prev = MESSAGES[conversationId] ?? [];
  const next = [...prev, userMsg, assistantMsg];
  MESSAGES[conversationId] = next;
  return next;
}
