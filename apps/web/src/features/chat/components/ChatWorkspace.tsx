"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
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
import { listAssets, uploadAsset } from "@/features/assets";
import { listKnowledgeBases } from "@/features/knowledge";
import { cn } from "@/lib/cn";
import {
  takePendingReferences,
  type PendingReferenceAsset,
} from "@/lib/pending-refs";
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
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKbIds, setSelectedKbIds] = useState<string[]>([]);
  const [pendingRefs, setPendingRefs] = useState<PendingReferenceAsset[]>([]);
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

  // 资产中心「送回对话」：query + sessionStorage
  useEffect(() => {
    let cancelled = false;
    const fromQuery = (searchParams.get("referenceAssetIds") || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .slice(0, 4);
    const fromStore = takePendingReferences(workspaceId);
    const idSet = new Set<string>([
      ...fromQuery,
      ...fromStore.map((a) => a.id),
    ]);
    if (!idSet.size) return;

    void (async () => {
      const byId = new Map(fromStore.map((a) => [a.id, a]));
      const missing = [...idSet].filter((id) => !byId.has(id));
      if (missing.length) {
        try {
          const all = await listAssets(workspaceId, "image");
          for (const asset of all) {
            if (idSet.has(asset.id)) {
              byId.set(asset.id, {
                id: asset.id,
                name: asset.name,
                thumbUrl: asset.thumbUrl || asset.url,
                url: asset.url,
              });
            }
          }
        } catch {
          // keep what we have
        }
      }
      if (cancelled) return;
      const next = [...idSet]
        .map((id) => byId.get(id))
        .filter(Boolean) as PendingReferenceAsset[];
      if (next.length) setPendingRefs(next);
      if (fromQuery.length) {
        router.replace(
          routes.chatConversation(workspaceId, activeConversationId),
        );
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [workspaceId, activeConversationId, searchParams, router]);

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

    const galleryPreviews: GenerationResult[] = pendingRefs.map((ref) => ({
      id: ref.id,
      label: "参考图",
      tone: "d",
      kind: "image",
      url: ref.thumbUrl || ref.url,
    }));
    const localPreviews: GenerationResult[] = files.map((file, i) => ({
      id: `local_ref_${i}`,
      label: "参考图",
      tone: "d",
      kind: "image",
      url: URL.createObjectURL(file),
    }));
    const allPreviews = [...galleryPreviews, ...localPreviews];

    const optimistic: ChatMessage = {
      id: `local_u_${Date.now()}`,
      role: "user",
      content: text,
      results: allPreviews.length ? allPreviews : undefined,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [
      ...prev.filter((m) => m.id !== "local_assistant_stream"),
      optimistic,
    ]);

    const galleryIds = pendingRefs.map((r) => r.id);

    try {
      const referenceAssetIds: string[] = [...galleryIds];
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
      setPendingRefs([]);
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
          {pendingRefs.length > 0 ? (
            <div className={styles.refBar}>
              <span className={styles.kbLabel}>待发送参考图</span>
              {pendingRefs.map((ref) => (
                <div key={ref.id} className={styles.refChip}>
                  {ref.thumbUrl || ref.url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={ref.thumbUrl || ref.url} alt={ref.name} />
                  ) : null}
                  <span>{ref.name}</span>
                  <button
                    type="button"
                    disabled={sending}
                    onClick={() =>
                      setPendingRefs((prev) =>
                        prev.filter((x) => x.id !== ref.id),
                      )
                    }
                  >
                    移除
                  </button>
                </div>
              ))}
            </div>
          ) : null}
          <div className={styles.messages}>
            {pending && messages.length === 0 ? (
              <p className={styles.hint}>加载对话…</p>
            ) : null}
            {showEmptyThread ? (
              <div className={styles.emptyBox}>
                <strong>从一句需求开始</strong>
                <p>
                  例如：「按参考图做商店页头图，再偏暖一点」。也可从资产中心点「送回对话」。
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
