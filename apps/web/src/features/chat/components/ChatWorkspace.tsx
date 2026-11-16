"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Panel from "@/components/ui/Panel";
import Button from "@/components/ui/Button";
import PageHeader from "@/components/ui/PageHeader";
import MessageBubble from "@/features/chat/components/MessageBubble";
import ChatComposer from "@/features/chat/components/ChatComposer";
import {
  createConversation,
  getConversationMessages,
  sendMessage,
} from "@/features/chat";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import type { ChatMessage, ConversationSummary } from "@/types/domain";
import styles from "./ChatWorkspace.module.css";

export interface ChatWorkspaceProps {
  workspaceId: string;
  conversations: ConversationSummary[];
  activeConversationId: string;
}

export default function ChatWorkspace({
  workspaceId,
  conversations,
  activeConversationId,
}: ChatWorkspaceProps) {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [pending, startTransition] = useTransition();

  const active = useMemo(
    () => conversations.find((c) => c.id === activeConversationId),
    [conversations, activeConversationId],
  );

  useEffect(() => {
    let cancelled = false;
    setError(null);
    startTransition(() => {
      void getConversationMessages(activeConversationId, workspaceId)
        .then((data) => {
          if (!cancelled) setMessages(data);
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : "加载对话失败");
          }
        });
    });
    return () => {
      cancelled = true;
    };
  }, [activeConversationId, workspaceId]);

  async function handleSend(text: string) {
    setError(null);
    setSending(true);
    const optimistic: ChatMessage = {
      id: `local_u_${Date.now()}`,
      role: "user",
      content: text,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    try {
      const next = await sendMessage(activeConversationId, text, workspaceId);
      setMessages(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送失败");
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id));
    } finally {
      setSending(false);
    }
  }

  async function handleNewChat() {
    setError(null);
    try {
      const created = await createConversation(workspaceId, "新对话");
      router.push(routes.chatConversation(workspaceId, created.id));
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "新建对话失败");
    }
  }

  return (
    <div className={`page-enter ${styles.wrap}`}>
      <PageHeader
        title="创作对话"
        description={
          active
            ? `${active.title} · 支持纯文本问答与生图/生视频`
            : "多轮迭代 · 自动归档到资产中心"
        }
        actions={
          <Button variant="ghost" onClick={() => void handleNewChat()}>
            新建对话
          </Button>
        }
      />

      <div className={styles.layout}>
        <Panel className={styles.sessions}>
          {conversations.length === 0 ? (
            <p className={styles.hint}>暂无会话，点右上角新建。</p>
          ) : null}
          {conversations.map((c) => (
            <Link
              key={c.id}
              href={routes.chatConversation(workspaceId, c.id)}
              className={cn(
                styles.session,
                c.id === activeConversationId && styles.sessionActive,
              )}
              onClick={(e) => {
                e.preventDefault();
                router.push(routes.chatConversation(workspaceId, c.id));
              }}
            >
              <strong>{c.title}</strong>
              <span>{c.updatedAtLabel}</span>
            </Link>
          ))}
        </Panel>

        <Panel className={styles.pane}>
          <div className={styles.messages}>
            {pending && messages.length === 0 ? (
              <p className={styles.hint}>加载对话…</p>
            ) : null}
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {sending ? <p className={styles.hint}>Prism 正在回复…</p> : null}
            {error ? <p className={styles.error}>{error}</p> : null}
          </div>
          <ChatComposer onSend={handleSend} disabled={sending} />
        </Panel>
      </div>
    </div>
  );
}
