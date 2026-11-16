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
import { uploadAsset } from "@/features/assets";
import { listKnowledgeBases } from "@/features/knowledge";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import type {
  ChatMessage,
  ConversationSummary,
  GenerationResult,
  KnowledgeBase,
} from "@/types/domain";
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

  function upsertStreamingAssistant(
    patch: Partial<ChatMessage> & { content?: string },
  ) {
    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === "local_assistant_stream");
      if (idx < 0) {
        return [
          ...prev,
          {
            id: "local_assistant_stream",
            role: "assistant",
            content: patch.content ?? "",
            toolLabel: patch.toolLabel,
            results: patch.results,
            createdAt: new Date().toISOString(),
            streaming: true,
          },
        ];
      }
      const copy = [...prev];
      copy[idx] = {
        ...copy[idx],
        ...patch,
        streaming: true,
      };
      return copy;
    });
  }

  async function handleSend(text: string, files: File[]) {
    setError(null);
    setSending(true);
    setStatusText(files.length ? "正在上传参考图…" : "正在理解意图…");

    const localPreviews: GenerationResult[] = files.map((file, i) => ({
      id: `local_ref_${i}`,
      label: "参考图",
      tone: "d",
      kind: "image",
      url: URL.createObjectURL(file),
    }));

    const optimistic: ChatMessage = {
      id: `local_u_${Date.now()}`,
      role: "user",
      content: text,
      results: localPreviews.length ? localPreviews : undefined,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [
      ...prev.filter((m) => m.id !== "local_assistant_stream"),
      optimistic,
    ]);

    try {
      const referenceAssetIds: string[] = [];
      for (const file of files) {
        const uploaded = await uploadAsset(workspaceId, file, {
          conversationId: activeConversationId,
        });
        referenceAssetIds.push(uploaded.id);
      }

      const next = await sendMessage(activeConversationId, text, {
        workspaceId,
        knowledgeBaseIds: selectedKbIds,
        referenceAssetIds,
        onProgress: (p) => {
          setStatusText(p.status);
          if (p.error) setError(p.error);
          if (
            p.content !== undefined ||
            p.results ||
            p.toolLabel ||
            p.done
          ) {
            upsertStreamingAssistant({
              content: p.content,
              toolLabel: p.toolLabel,
              results: p.results,
            });
          }
        },
      });
      setMessages(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送失败，请稍后重试");
      setMessages((prev) =>
        prev.filter(
          (m) => m.id !== optimistic.id && m.id !== "local_assistant_stream",
        ),
      );
    } finally {
      for (const item of localPreviews) {
        if (item.url?.startsWith("blob:")) URL.revokeObjectURL(item.url);
      }
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

  const showEmptyThread =
    !pending && !sending && messages.length === 0 && !error;

  return (
    <div className={`page-enter ${styles.wrap}`}>
      <PageHeader
        title="创作对话"
        description={
          active
            ? `${active.title} · 问答 / 生图 / 生视频 / 参考图改稿`
            : "问答 / 生图 / 生视频 / 参考图改稿"
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
            <div className={styles.emptyBox}>
              <strong>还没有会话</strong>
              <p>点右上角「新建对话」，从一句 brief 开始。</p>
            </div>
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
              <span className={styles.hint}>
                当前空间暂无知识库 · 可先去知识库页创建
              </span>
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
            {showEmptyThread ? (
              <div className={styles.emptyBox}>
                <strong>从一句需求开始</strong>
                <p>
                  例如：「按参考图做商店页头图，再偏暖一点」或「根据知识库写发行
                  brief」。也可以先点下方「附参考图」。
                </p>
              </div>
            ) : null}
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {error ? (
              <div className={styles.error} role="alert">
                <strong>出错了</strong>
                <p>{error}</p>
                <button
                  type="button"
                  className={styles.errorDismiss}
                  onClick={() => setError(null)}
                >
                  知道了
                </button>
              </div>
            ) : null}
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
