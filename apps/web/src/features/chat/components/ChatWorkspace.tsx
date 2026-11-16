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
  const [pending, startTransition] = useTransition();

  const active = useMemo(
    () => conversations.find((c) => c.id === activeConversationId),
    [conversations, activeConversationId],
  );

  useEffect(() => {
    let cancelled = false;
    startTransition(() => {
      void getConversationMessages(activeConversationId).then((data) => {
        if (!cancelled) {
          setMessages(data);
        }
      });
    });
    return () => {
      cancelled = true;
    };
  }, [activeConversationId]);

  async function handleSend(text: string) {
    const next = await sendMessage(activeConversationId, text);
    setMessages(next);
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
        actions={<Button variant="ghost">引用知识库</Button>}
      />

      <div className={styles.layout}>
        <Panel className={styles.sessions}>
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
          </div>
          <ChatComposer onSend={handleSend} />
        </Panel>
      </div>
    </div>
  );
}
