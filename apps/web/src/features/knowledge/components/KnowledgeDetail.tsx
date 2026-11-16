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
  const [tab, setTab] = useState<SearchTab>("image");
  const [query, setQuery] = useState("春季 · 青石主色 · 横版");
  const [hits, setHits] = useState(initialHits);
  const [pending, startTransition] = useTransition();

  function runSearch() {
    startTransition(() => {
      void (tab === "image"
        ? searchByImage(knowledgeBase.id, query)
        : searchByText(knowledgeBase.id, query)
      ).then(setHits);
    });
  }

  return (
    <div className="page-enter">
      <PageHeader
        title={knowledgeBase.name}
        description="文本检索 · 以图搜图"
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
              className={cn(styles.tab, tab === "image" && styles.tabActive)}
              onClick={() => setTab("image")}
            >
              以图搜图
            </button>
            <button
              type="button"
              className={cn(styles.tab, tab === "text" && styles.tabActive)}
              onClick={() => setTab("text")}
            >
              文本检索
            </button>
            <button type="button" className={styles.tab} disabled>
              片段检索
            </button>
          </div>

          {tab === "image" ? (
            <div className={styles.dropzone}>
              拖入参考图，或 <strong>点击上传</strong>
              <br />
              <span>JPG / PNG · 用于相似素材召回（演示）</span>
            </div>
          ) : null}

          <div className={styles.search}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={tab === "image" ? "补充检索提示（可选）" : "输入问题或关键词"}
            />
            <Button onClick={runSearch} disabled={pending}>
              {pending ? "检索中…" : "搜索"}
            </Button>
          </div>
          <p className={styles.note}>
            片段检索（Phase 2）将支持按镜头定位视频时间段。
          </p>
        </Panel>

        <div className={styles.hits}>
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
