"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import Panel from "@/components/ui/Panel";
import { searchByImage, searchByText } from "@/features/knowledge";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import type { KnowledgeBase, KnowledgeHit } from "@/types/domain";
import styles from "./KnowledgeDetail.module.css";

export type SearchTab = "image" | "text";

export interface KnowledgeDetailProps {
  workspaceId: string;
  knowledgeBase: KnowledgeBase;
  initialHits: KnowledgeHit[];
}

export default function KnowledgeDetail({
  workspaceId,
  knowledgeBase,
  initialHits,
}: KnowledgeDetailProps) {
  const [tab, setTab] = useState<SearchTab>("text");
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState(initialHits);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function runSearch() {
    const q = query.trim();
    if (!q) {
      setError(tab === "image" ? "请输入图片描述关键词" : "请输入检索关键词");
      return;
    }
    setError(null);
    startTransition(() => {
      void (tab === "image"
        ? searchByImage(knowledgeBase.id, q, workspaceId)
        : searchByText(knowledgeBase.id, q, workspaceId)
      )
        .then(setHits)
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "检索失败");
        });
    });
  }

  return (
    <div className="page-enter">
      <PageHeader
        title={knowledgeBase.name}
        description={`${knowledgeBase.documentCount} 文档 · ${knowledgeBase.imageCount} 图片 · 当前可文本检索 / 以文搜图`}
        actions={
          <Link href={routes.knowledge(workspaceId)}>
            <Button variant="ghost">返回列表</Button>
          </Link>
        }
      />

      <div className={styles.layout}>
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
              className={cn(styles.tab, tab === "image" && styles.tabActive)}
              onClick={() => setTab("image")}
            >
              以文搜图
            </button>
            <button type="button" className={styles.tab} disabled>
              片段检索 · 未上线
            </button>
          </div>

          {tab === "image" ? (
            <div className={styles.notice}>
              真·上传图片搜图尚未开放。这里用<strong>文字描述</strong>在图片素材里做相似召回（需已配置向量模型）。
            </div>
          ) : (
            <div className={styles.notice}>
              在已入库文档中做语义/关键词检索。网页上传 PDF/图片入库接口稍后补齐。
            </div>
          )}

          <div className={styles.search}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                tab === "image"
                  ? "例如：春季主视觉、青石色包装"
                  : "例如：品牌主色规范"
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") runSearch();
              }}
            />
            <Button onClick={runSearch} disabled={pending}>
              {pending ? "检索中…" : "搜索"}
            </Button>
          </div>
          {error ? <p className={styles.error}>{error}</p> : null}
          <p className={styles.note}>
            视频片段检索（Phase 2）将支持按镜头定位时间段。
          </p>
        </Panel>

        <div className={styles.hits}>
          {hits.length === 0 ? (
            <Panel className={styles.emptyHits}>
              <p>暂无命中。换个关键词，或确认知识库里已有文档/图片条目。</p>
            </Panel>
          ) : null}
          {hits.map((hit) => (
            <div key={hit.id} className={styles.hit}>
              <div className={cn(styles.preview, `thumb-${hit.tone}`)} />
              <div>
                <h4>{hit.title}</h4>
                <p>{hit.summary}</p>
                <span className={styles.score}>相似 {hit.score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
