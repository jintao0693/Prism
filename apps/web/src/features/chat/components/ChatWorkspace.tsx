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
import { listKnowledgeBases } from "@/features/knowledge";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import type { ChatMessage, ConversationSummary, KnowledgeBase } from "@/types/domain";
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
  const [statusText, setStatusText] = useState<string | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKbIds, setSelectedKbIds] = useState<string[]>([]);
  const [pending, startTransition] = useTransition();

  const active = useMemo(
    () => conversations.find((c) => c.id === activeConversationId),
    [conversations, activeConversationId],
  );

  useEffect(() => {
    let cancelled = false;
    void listKnowledgeBases(workspaceId)
      .then((bases) => {
        if (!cancelled) setKnowledgeBases(bases);
      })
      .catch(() => {
        if (!cancelled) setKnowledgeBases([]);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

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

  function toggleKb(id: string) {
    setSelectedKbIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function handleSend(text: string) {
    setError(null);
    setSending(true);
    setStatusText("正在理解意图…");
    const optimistic: ChatMessage = {
      id: `local_u_${Date.now()}`,
      role: "user",
      content: text,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    try {
      const next = await sendMessage(activeConversationId, text, {
        workspaceId,
        knowledgeBaseIds: selectedKbIds,
        onProgress: (p) => setStatusText(p.status),
      });
      setMessages(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送失败");
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id));
    } finally {
      setSending(false);
      setStatusText(null);
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
            ? `${active.title} · 文本问答 / 生图 / 生视频（自动识别意图）`
            : "文本问答 / 生图 / 生视频（自动识别意图）"
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
          <div className={styles.kbBar}>
            <span className={styles.kbLabel}>引用知识库</span>
            {knowledgeBases.length === 0 ? (
              <span className={styles.hint}>当前空间暂无知识库</span>
            ) : (
              knowledgeBases.map((kb) => (
                <label key={kb.id} className={styles.kbChip}>
                  <input
                    type="checkbox"
                    checked={selectedKbIds.includes(kb.id)}
                    onChange={() => toggleKb(kb.id)}
                    disabled={sending}
                  />
                  {kb.name}
                </label>
              ))
            )}
          </div>
          <div className={styles.messages}>
            {pending && messages.length === 0 ? (
              <p className={styles.hint}>加载对话…</p>
            ) : null}
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {sending && statusText ? (
              <p className={styles.hint}>{statusText}</p>
            ) : null}
            {error ? <p className={styles.error}>{error}</p> : null}
          </div>
          <ChatComposer
            onSend={handleSend}
            disabled={sending}
            statusText={sending ? statusText : null}
          />
        </Panel>
      </div>
    </div>
  );
}
