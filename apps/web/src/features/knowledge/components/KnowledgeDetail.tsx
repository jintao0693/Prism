"use client";

import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import Panel from "@/components/ui/Panel";
import {
  getKnowledgeBase,
  ingestDocument,
  ingestImage,
  listKnowledgeItems,
  mapWithConcurrency,
  reembedItem,
  reembedMissing,
  searchByImage,
  searchByImageFile,
  searchByText,
} from "@/features/knowledge";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import type {
  KnowledgeBase,
  KnowledgeHit,
  KnowledgeItem,
} from "@/types/domain";
import styles from "./KnowledgeDetail.module.css";

export type SearchTab = "text" | "text2img" | "img2img";

export interface KnowledgeDetailProps {
  workspaceId: string;
  knowledgeBase: KnowledgeBase;
  initialHits: KnowledgeHit[];
}

export default function KnowledgeDetail({
  workspaceId,
  knowledgeBase: initialKb,
  initialHits,
}: KnowledgeDetailProps) {
  const router = useRouter();
  const [kb, setKb] = useState(initialKb);
  const [tab, setTab] = useState<SearchTab>("text");
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState(initialHits);
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [queryFile, setQueryFile] = useState<File | null>(null);
  const [queryPreview, setQueryPreview] = useState<string | null>(null);
  const [docTitle, setDocTitle] = useState("");
  const [docContent, setDocContent] = useState("");
  const [uploadProgress, setUploadProgress] = useState<{
    done: number;
    total: number;
    name: string;
  } | null>(null);
  const [reembeddingId, setReembeddingId] = useState<string | null>(null);
  const uploadRef = useRef<HTMLInputElement>(null);
  const queryImgRef = useRef<HTMLInputElement>(null);

  const missingCount = items.filter((i) => !i.hasEmbedding).length;

  const refreshMeta = useCallback(async () => {
    const [nextKb, nextItems] = await Promise.all([
      getKnowledgeBase(kb.id, workspaceId),
      listKnowledgeItems(kb.id, workspaceId),
    ]);
    setKb(nextKb);
    setItems(nextItems);
  }, [kb.id, workspaceId]);

  useEffect(() => {
    void refreshMeta().catch(() => {
      /* 列表失败时保留空态，不打断页面 */
    });
  }, [refreshMeta]);

  useEffect(() => {
    if (!queryFile) {
      setQueryPreview(null);
      return;
    }
    const url = URL.createObjectURL(queryFile);
    setQueryPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [queryFile]);

  function runSearch() {
    setError(null);
    setStatus(null);

    if (tab === "img2img") {
      if (!queryFile) {
        setError("请先选择一张参考图");
        return;
      }
      const file = queryFile;
      const hint = query.trim() || undefined;
      startTransition(() => {
        void searchByImageFile(kb.id, file, workspaceId, hint)
          .then((next) => {
            setHits(next);
            setStatus(next.length ? `找到 ${next.length} 条相似图片` : "没有相似命中");
          })
          .catch((err: unknown) => {
            setError(err instanceof Error ? err.message : "以图搜图失败");
          });
      });
      return;
    }

    const q = query.trim();
    if (!q) {
      setError(tab === "text2img" ? "请输入图片描述关键词" : "请输入检索关键词");
      return;
    }
    startTransition(() => {
      void (tab === "text2img"
        ? searchByImage(kb.id, q, workspaceId)
        : searchByText(kb.id, q, workspaceId)
      )
        .then((next) => {
          setHits(next);
          setStatus(next.length ? `找到 ${next.length} 条结果` : "没有命中");
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "检索失败");
        });
    });
  }

  function handleUploadImages(files: FileList | null) {
    if (!files?.length) return;
    const list = Array.from(files).slice(0, 40);
    setError(null);
    setUploadProgress({ done: 0, total: list.length, name: list[0]?.name ?? "" });
    setStatus(`正在入库 0/${list.length}…`);
    startTransition(() => {
      void (async () => {
        let embedded = 0;
        const results = await mapWithConcurrency(
          list,
          3,
          async (file) => {
            const item = await ingestImage(kb.id, workspaceId, file);
            if (item.hasEmbedding) embedded += 1;
            return item;
          },
          (done, total, file) => {
            setUploadProgress({ done, total, name: file.name });
            setStatus(`正在入库 ${done}/${total} · ${file.name}`);
          },
        );
        await refreshMeta();
        setUploadProgress(null);
        setStatus(
          `已入库 ${results.length} 张图片` +
            (embedded
              ? `（${embedded} 张已写入向量，并发 3）`
              : "（未写入向量：请检查 Embedding 或点「补齐向量」）"),
        );
      })().catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "图片入库失败");
        setStatus(null);
        setUploadProgress(null);
      });
    });
  }

  function handleReembedOne(item: KnowledgeItem) {
    setError(null);
    setReembeddingId(item.id);
    startTransition(() => {
      void reembedItem(kb.id, item.id, workspaceId)
        .then(async () => {
          await refreshMeta();
          setStatus(`已重新向量化：${item.title}`);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "重新向量化失败");
        })
        .finally(() => setReembeddingId(null));
    });
  }

  function handleReembedMissing() {
    if (!missingCount) {
      setStatus("没有缺少向量的条目");
      return;
    }
    setError(null);
    setStatus(`正在补齐 ${missingCount} 条向量…`);
    startTransition(() => {
      void reembedMissing(kb.id, workspaceId)
        .then(async (res) => {
          await refreshMeta();
          setStatus(
            `补齐完成：成功 ${res.ok}/${res.attempted}` +
              (res.failed.length
                ? `，失败 ${res.failed.length}（如图片过小）`
                : ""),
          );
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "批量补齐失败");
          setStatus(null);
        });
    });
  }

  function handleIngestDoc() {
    const title = docTitle.trim();
    const content = docContent.trim();
    if (!title || !content) {
      setError("文档标题和正文都不能为空");
      return;
    }
    setError(null);
    setStatus("正在写入文档…");
    startTransition(() => {
      void ingestDocument(kb.id, workspaceId, title, content)
        .then(async (res) => {
          setDocTitle("");
          setDocContent("");
          await refreshMeta();
          setStatus(
            res.hasEmbedding
              ? "文档已入库并写入向量"
              : "文档已入库（未写入向量：请检查 Embedding 配置）",
          );
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "文档入库失败");
          setStatus(null);
        });
    });
  }

  return (
    <div className="page-enter">
      <PageHeader
        title={kb.name}
        description={`${kb.documentCount} 文档 · ${kb.imageCount} 图片 · 支持文本检索 / 以文搜图 / 以图搜图`}
        actions={
          <Link href={routes.knowledge(workspaceId)}>
            <Button variant="ghost">返回列表</Button>
          </Link>
        }
      />

      <div className={styles.layout}>
        <div className={styles.leftCol}>
          <Panel className={styles.left}>
            <div className={styles.tabs}>
              <button
                type="button"
                className={cn(styles.tab, tab === "text" && styles.tabActive)}
                onClick={() => setTab("text")}
              >
                文本检索
              </button>
              <button
                type="button"
                className={cn(styles.tab, tab === "text2img" && styles.tabActive)}
                onClick={() => setTab("text2img")}
              >
                以文搜图
              </button>
              <button
                type="button"
                className={cn(styles.tab, tab === "img2img" && styles.tabActive)}
                onClick={() => setTab("img2img")}
              >
                以图搜图
              </button>
            </div>

            {tab === "img2img" ? (
              <div className={styles.notice}>
                选一张参考图，在库里找视觉相近的素材；可顺手补一句描述帮排序。
              </div>
            ) : tab === "text2img" ? (
              <div className={styles.notice}>
                用一句话描述想找的画面，在已入库图片里召回。
              </div>
            ) : (
              <div className={styles.notice}>
                按意思搜文档与设定，不必精确记关键词。
              </div>
            )}

            {tab === "img2img" ? (
              <div className={styles.queryImage}>
                <input
                  ref={queryImgRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  hidden
                  onChange={(e) => {
                    setQueryFile(e.target.files?.[0] ?? null);
                    e.target.value = "";
                  }}
                />
                {queryPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={queryPreview}
                    alt="参考图预览"
                    className={styles.queryPreview}
                  />
                ) : (
                  <button
                    type="button"
                    className={styles.dropzone}
                    onClick={() => queryImgRef.current?.click()}
                  >
                    选择参考图
                  </button>
                )}
                <div className={styles.queryImageActions}>
                  <Button
                    variant="ghost"
                    onClick={() => queryImgRef.current?.click()}
                  >
                    {queryFile ? "更换" : "选择图片"}
                  </Button>
                  {queryFile ? (
                    <Button
                      variant="ghost"
                      onClick={() => setQueryFile(null)}
                    >
                      清除
                    </Button>
                  ) : null}
                </div>
              </div>
            ) : null}

            <div className={styles.search}>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  tab === "img2img"
                    ? "可选：补充描述，如春季主视觉"
                    : tab === "text2img"
                      ? "例如：春季主视觉、青石色包装"
                      : "例如：品牌主色规范"
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") runSearch();
                }}
              />
              <Button onClick={runSearch} disabled={pending}>
                {pending ? "处理中…" : "搜索"}
              </Button>
            </div>
            {error ? <p className={styles.error}>{error}</p> : null}
            {status ? <p className={styles.status}>{status}</p> : null}
          </Panel>

          <Panel className={styles.ingest}>
            <h3>入库</h3>
            <p className={styles.ingestHint}>
              上传图片或粘贴文档后会自动写入向量，便于对话引用与检索。右侧可查看每条是否已向量化。
            </p>
            <input
              ref={uploadRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              multiple
              hidden
              onChange={(e) => {
                handleUploadImages(e.target.files);
                e.target.value = "";
              }}
            />
            <div className={styles.ingestActions}>
              <Button
                onClick={() => uploadRef.current?.click()}
                disabled={pending}
              >
                上传图片（最多 40，并发 3）
              </Button>
              <Button
                variant="ghost"
                onClick={handleReembedMissing}
                disabled={pending || missingCount === 0}
              >
                补齐向量{missingCount ? ` (${missingCount})` : ""}
              </Button>
            </div>
            {uploadProgress ? (
              <div className={styles.progressWrap}>
                <div className={styles.progressBar}>
                  <div
                    className={styles.progressFill}
                    style={{
                      width: `${Math.round(
                        (uploadProgress.done / Math.max(uploadProgress.total, 1)) *
                          100,
                      )}%`,
                    }}
                  />
                </div>
                <p className={styles.progressLabel}>
                  {uploadProgress.done}/{uploadProgress.total} · {uploadProgress.name}
                </p>
              </div>
            ) : null}
            <div className={styles.docForm}>
              <input
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                placeholder="文档标题"
              />
              <textarea
                value={docContent}
                onChange={(e) => setDocContent(e.target.value)}
                placeholder="粘贴文档正文…"
                rows={4}
              />
              <Button onClick={handleIngestDoc} disabled={pending}>
                写入文档
              </Button>
            </div>
          </Panel>
        </div>

        <div className={styles.rightCol}>
          <div className={styles.hits}>
            <h3 className={styles.sectionTitle}>检索结果</h3>
            {hits.length === 0 ? (
              <Panel className={styles.emptyHits}>
                <p>还没有命中。先往库里放点素材，再选一种方式搜索。</p>
              </Panel>
            ) : null}
            {hits.map((hit) => (
              <HitCard
                key={hit.id}
                hit={hit}
                workspaceId={workspaceId}
                kbName={kb.name}
                routerPush={(href) => router.push(href)}
              />
            ))}
          </div>

          <div className={styles.items}>
            <h3 className={styles.sectionTitle}>
              库内条目
              <span className={styles.count}>{items.length}</span>
            </h3>
            {items.length === 0 ? (
              <Panel className={styles.emptyHits}>
                <p>还没有条目。上传图片或写入文档后会出现在这里。</p>
              </Panel>
            ) : null}
            <div className={styles.itemGrid}>
              {items.map((item) => (
                <div key={item.id} className={styles.item}>
                  {item.itemType === "image" && (item.thumbUrl || item.url) ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={item.thumbUrl || item.url}
                      alt={item.title}
                      className={styles.itemThumb}
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div
                      className={cn(
                        styles.itemThumb,
                        styles.itemDoc,
                        item.itemType === "image" && "thumb-a",
                      )}
                    />
                  )}
                  <div className={styles.itemMeta}>
                    <strong>{item.title}</strong>
                    <span>
                      {item.itemType === "image" ? "图片" : "文档"}
                      {item.hasEmbedding ? " · 已向量化" : " · 无向量"}
                    </span>
                    {!item.hasEmbedding ? (
                      <button
                        type="button"
                        className={styles.reembedBtn}
                        disabled={pending || reembeddingId === item.id}
                        onClick={() => handleReembedOne(item)}
                      >
                        {reembeddingId === item.id ? "向量化中…" : "重新向量化"}
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function HitCard({
  hit,
  workspaceId,
  kbName,
  routerPush,
}: {
  hit: KnowledgeHit;
  workspaceId: string;
  kbName: string;
  routerPush: (href: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  async function sendToChat() {
    if (busy) return;
    setBusy(true);
    setSendError(null);
    try {
      const { createConversation } = await import("@/features/chat");
      const { stashComposerDraft } = await import("@/lib/pending-draft");
      const draft = [
        `请基于知识库「${kbName}」中的资料回答 / 创作：`,
        `标题：${hit.title}`,
        hit.summary ? `摘要：${hit.summary}` : "",
      ]
        .filter(Boolean)
        .join("\n");
      stashComposerDraft(workspaceId, draft);
      const created = await createConversation(
        workspaceId,
        hit.title.slice(0, 28) || "知识库创作",
      );
      routerPush(routes.chatConversation(workspaceId, created.id));
    } catch (err: unknown) {
      setSendError(err instanceof Error ? err.message : "带回对话失败，请重试");
      setBusy(false);
    }
  }

  return (
    <div className={styles.hit}>
      {hit.thumbUrl || hit.url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={hit.thumbUrl || hit.url}
          alt={hit.title}
          className={styles.previewImg}
          loading="lazy"
          decoding="async"
        />
      ) : (
        <div className={cn(styles.preview, `thumb-${hit.tone}`)} />
      )}
      <div>
        <h4>{hit.title}</h4>
        <p>{hit.summary}</p>
        <span className={styles.score}>相似 {hit.score.toFixed(2)}</span>
        {hit.itemType ? (
          <span className={styles.badge}>
            {hit.itemType === "image" ? "图片" : "文档"}
          </span>
        ) : null}
        <button
          type="button"
          className={styles.sendBtn}
          disabled={busy}
          onClick={() => void sendToChat()}
        >
          {busy ? "跳转中…" : "带回对话"}
        </button>
        {sendError ? (
          <p className={styles.sendError} role="alert">
            {sendError}
          </p>
        ) : null}
      </div>
    </div>
  );
}
