"use client";

import { useEffect, useMemo, useRef, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import Panel from "@/components/ui/Panel";
import Button from "@/components/ui/Button";
import PageHeader from "@/components/ui/PageHeader";
import MessageBubble from "@/features/chat/components/MessageBubble";
import ChatComposer from "@/features/chat/components/ChatComposer";
import {
  compactConversation,
  createConversation,
  deleteConversation,
  getConversationDetail,
  getConversationMessages,
  renameConversation,
  sendMessage,
  type ConversationDetail,
} from "@/features/chat";
import { listAssets, uploadAsset } from "@/features/assets";
import { listKnowledgeBases } from "@/features/knowledge";
import { getUsageSummary } from "@/features/workspace";
import { cn } from "@/lib/cn";
import {
  resolveDefaultKbSelection,
  saveKbSelection,
} from "@/lib/kb-prefs";
import { takeComposerDraft } from "@/lib/pending-draft";
import {
  takePendingReferences,
  type PendingReferenceAsset,
} from "@/lib/pending-refs";
import { formatQuotaHint } from "@/lib/quota-hint";
import { routes } from "@/lib/routes";
import type {
  ChatMessage,
  ConversationSummary,
  GenerationResult,
  KnowledgeBase,
  UsageSummary,
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
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [titleOverrides, setTitleOverrides] = useState<Record<string, string>>(
    {},
  );
  const [sessionQuery, setSessionQuery] = useState("");
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [compacting, setCompacting] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [draftText, setDraftText] = useState<string | null>(null);
  const [draftNonce, setDraftNonce] = useState(0);
  const [pending, startTransition] = useTransition();
  const messagesRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const sessionList = useMemo(() => {
    const q = sessionQuery.trim().toLowerCase();
    return conversations
      .map((c) => ({
        ...c,
        title: titleOverrides[c.id] || c.title,
      }))
      .filter((c) => !q || c.title.toLowerCase().includes(q));
  }, [conversations, titleOverrides, sessionQuery]);

  const active = useMemo(
    () =>
      sessionList.find((c) => c.id === activeConversationId) ||
      conversations.find((c) => c.id === activeConversationId),
    [sessionList, conversations, activeConversationId],
  );

  const quotaHint = useMemo(() => formatQuotaHint(usage), [usage]);

  useEffect(() => {
    let cancelled = false;
    void listKnowledgeBases(workspaceId)
      .then((bases) => {
        if (cancelled) return;
        setKnowledgeBases(bases);
        const names: Record<string, string> = {};
        for (const b of bases) names[b.id] = b.name;
        setSelectedKbIds(
          resolveDefaultKbSelection(
            workspaceId,
            bases.map((b) => b.id),
            names,
          ),
        );
      })
      .catch(() => {
        if (!cancelled) {
          setKnowledgeBases([]);
          setSelectedKbIds([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  useEffect(() => {
    let cancelled = false;
    void getUsageSummary()
      .then((data) => {
        if (!cancelled) setUsage(data);
      })
      .catch(() => {
        if (!cancelled) setUsage(null);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  useEffect(() => {
    const el = bottomRef.current;
    if (!el) return;
    el.scrollIntoView({ behavior: sending ? "smooth" : "auto", block: "end" });
  }, [messages, statusText, sending, pendingRefs, error]);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setActiveJobId(null);
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
      void getConversationDetail(activeConversationId, workspaceId)
        .then((d) => {
          if (!cancelled) setDetail(d);
        })
        .catch(() => {
          if (!cancelled) setDetail(null);
        });
    });
    const draft = takeComposerDraft(workspaceId);
    if (draft) {
      setDraftText(draft);
      setDraftNonce((n) => n + 1);
    }
    return () => {
      cancelled = true;
    };
  }, [activeConversationId, workspaceId]);

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
    setSelectedKbIds((prev) => {
      const next = prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id];
      saveKbSelection(workspaceId, next);
      return next;
    });
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

  function injectDraft(text: string) {
    setDraftText(text);
    setDraftNonce((n) => n + 1);
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
      ...prev.filter(
        (m) =>
          m.id !== "local_assistant_stream" &&
          !(m.failed && m.role === "user"),
      ),
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
          if (p.jobId) setActiveJobId(p.jobId);
          if (p.conversationTitle) {
            setTitleOverrides((prev) => ({
              ...prev,
              [activeConversationId]: p.conversationTitle!,
            }));
          }
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
      void getUsageSummary()
        .then(setUsage)
        .catch(() => undefined);
      void getConversationDetail(activeConversationId, workspaceId)
        .then(setDetail)
        .catch(() => undefined);
      router.refresh();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "发送失败，请稍后重试";
      setError(msg);
      setMessages((prev) =>
        prev
          .filter((m) => m.id !== "local_assistant_stream")
          .map((m) =>
            m.id === optimistic.id ? { ...m, failed: true } : m,
          ),
      );
      injectDraft(text);
    } finally {
      for (const item of localPreviews) {
        if (item.url?.startsWith("blob:")) URL.revokeObjectURL(item.url);
      }
      setSending(false);
      setStatusText(null);
    }
  }

  function handleRetryFailed() {
    const failed = [...messages].reverse().find((m) => m.failed && m.role === "user");
    if (!failed) return;
    injectDraft(failed.content);
    setMessages((prev) => prev.filter((m) => m.id !== failed.id));
    setError(null);
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

  async function handleRename(c: ConversationSummary) {
    const next = window.prompt("重命名会话", c.title);
    if (!next || !next.trim() || next.trim() === c.title) return;
    try {
      const updated = await renameConversation(
        c.id,
        workspaceId,
        next.trim(),
      );
      setTitleOverrides((prev) => ({ ...prev, [c.id]: updated.title }));
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "重命名失败");
    }
  }

  async function handleDelete(c: ConversationSummary) {
    if (!window.confirm(`删除会话「${c.title}」？此操作不可恢复。`)) return;
    try {
      await deleteConversation(c.id, workspaceId);
      if (c.id === activeConversationId) {
        const rest = conversations.filter((x) => x.id !== c.id);
        if (rest[0]) {
          router.push(routes.chatConversation(workspaceId, rest[0].id));
        } else {
          const created = await createConversation(workspaceId, "新对话");
          router.push(routes.chatConversation(workspaceId, created.id));
        }
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  async function handleCompact() {
    setCompacting(true);
    setError(null);
    try {
      const result = await compactConversation(
        activeConversationId,
        workspaceId,
      );
      setStatusText(
        result.didCompact
          ? `已整理上下文（第 ${result.generation} 次）`
          : result.reason || "当前无需压缩",
      );
      const d = await getConversationDetail(
        activeConversationId,
        workspaceId,
      );
      setDetail(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "整理会话失败");
    } finally {
      setCompacting(false);
      setTimeout(() => setStatusText(null), 2500);
    }
  }

  const showEmptyThread =
    !pending && !sending && messages.length === 0 && !error;

  return (
    <div className={`page-enter ${styles.wrap}`}>
      <PageHeader
        className={styles.header}
        title="创作对话"
        description={
          active
            ? `${active.title} · 问答 / 生图 / 生视频 / 参考图改稿`
            : "问答 / 生图 / 生视频 / 参考图改稿"
        }
        actions={
          <>
            <Button
              variant="ghost"
              disabled={compacting || sending}
              onClick={() => void handleCompact()}
            >
              {compacting ? "整理中…" : "整理会话"}
            </Button>
            <Button variant="ghost" onClick={() => void handleNewChat()}>
              新建对话
            </Button>
          </>
        }
      />

      <div className={styles.layout}>
        <Panel className={styles.sessions}>
          <div className={styles.sessionTools}>
            <input
              className={styles.sessionSearch}
              value={sessionQuery}
              onChange={(e) => setSessionQuery(e.target.value)}
              placeholder="搜索会话…"
            />
          </div>
          {sessionList.length === 0 ? (
            <div className={styles.emptyBox}>
              <strong>没有匹配会话</strong>
              <p>换个关键词，或点右上角新建对话。</p>
            </div>
          ) : null}
          {sessionList.map((c) => (
            <div
              key={c.id}
              className={cn(
                styles.sessionRow,
                c.id === activeConversationId && styles.sessionActive,
              )}
            >
              <Link
                href={routes.chatConversation(workspaceId, c.id)}
                className={styles.session}
                onClick={(e) => {
                  e.preventDefault();
                  router.push(routes.chatConversation(workspaceId, c.id));
                }}
              >
                <strong>{c.title}</strong>
                <span>
                  {c.kind === "video"
                    ? "视频"
                    : c.kind === "image"
                      ? "图片"
                      : "对话"}{" "}
                  · {c.updatedAtLabel}
                </span>
              </Link>
              <div className={styles.sessionActions}>
                <button
                  type="button"
                  title="重命名"
                  onClick={() => void handleRename(c)}
                >
                  改
                </button>
                <button
                  type="button"
                  title="删除"
                  onClick={() => void handleDelete(c)}
                >
                  删
                </button>
              </div>
            </div>
          ))}
        </Panel>

        <Panel className={styles.pane}>
          {detail?.summaryText ? (
            <div className={styles.compactBanner}>
              <strong>已整理摘要 · 第 {detail.compactGeneration || 1} 次</strong>
              <p>{detail.summaryText.slice(0, 180)}{detail.summaryText.length > 180 ? "…" : ""}</p>
            </div>
          ) : null}
          {activeJobId ? (
            <div className={styles.jobBanner}>
              视频任务进行中，关闭页面也可稍后在{" "}
              <Link href={routes.jobs(workspaceId)}>任务中心</Link> 查看进度（
              {activeJobId.slice(0, 10)}…）
            </div>
          ) : null}
          <div className={styles.messages} ref={messagesRef}>
            {pending && messages.length === 0 ? (
              <p className={styles.hint}>加载对话…</p>
            ) : null}
            {showEmptyThread ? (
              <div className={styles.emptyBox}>
                <strong>从一句需求开始</strong>
                <p>
                  例如：「按参考图做商店页头图，再偏暖一点」。也可从资产中心点「送回对话」；需要设定问答时在下方勾选知识库。
                </p>
              </div>
            ) : null}
            {messages.map((m) => (
              <MessageBubble
                key={m.id}
                message={m}
                onRetry={m.failed ? handleRetryFailed : undefined}
              />
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
            <div ref={bottomRef} className={styles.scrollAnchor} aria-hidden />
          </div>
          <div className={styles.composerDock}>
            <ChatComposer
              onSend={handleSend}
              disabled={sending}
              statusText={sending ? statusText : null}
              quotaHint={!sending ? quotaHint : null}
              draftText={draftText}
              draftNonce={draftNonce}
              knowledgeBases={knowledgeBases}
              selectedKbIds={selectedKbIds}
              onToggleKb={toggleKb}
              pendingRefs={pendingRefs}
              onRemovePendingRef={(id) =>
                setPendingRefs((prev) => prev.filter((x) => x.id !== id))
              }
              kbEmptyHint={
                <>
                  暂无知识库 ·{" "}
                  <Link href={routes.knowledge(workspaceId)}>去创建</Link>
                </>
              }
            />
          </div>
        </Panel>
      </div>
    </div>
  );
}
