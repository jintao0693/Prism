"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import Panel from "@/components/ui/Panel";
import SpectrumBar from "@/components/ui/SpectrumBar";
import { createKnowledgeBase } from "@/features/knowledge";
import { routes } from "@/lib/routes";
import type { KnowledgeBase } from "@/types/domain";
import styles from "./KnowledgeList.module.css";

export interface KnowledgeListProps {
  workspaceId: string;
  bases: KnowledgeBase[];
}

export default function KnowledgeList({
  workspaceId,
  bases,
}: KnowledgeListProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleCreate() {
    setError(null);
    startTransition(() => {
      void createKnowledgeBase(workspaceId, "新知识库", "当前工作空间素材与文档")
        .then((kb) => {
          router.push(routes.knowledgeDetail(workspaceId, kb.id));
          router.refresh();
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "创建失败");
        });
    });
  }

  return (
    <div className="page-enter">
      <PageHeader
        title="知识库"
        description="已支持：文本检索、以文搜图。上传文件/真·以图搜图/视频片段检索尚未上线。"
        actions={
          <Button onClick={handleCreate} disabled={pending}>
            {pending ? "创建中…" : "新建知识库"}
          </Button>
        }
      />
      {error ? <p className={styles.error}>{error}</p> : null}
      <div className={styles.grid}>
        {bases.length === 0 ? (
          <Panel className={styles.empty}>
            <h3>还没有知识库</h3>
            <p>先新建一个，再在详情页用关键词检索种子/入库文档。</p>
          </Panel>
        ) : null}
        {bases.map((kb) => (
          <Link
            key={kb.id}
            href={routes.knowledgeDetail(workspaceId, kb.id)}
            className={styles.cardLink}
          >
            <Panel className={styles.card}>
              <SpectrumBar width={48} />
              <h3>{kb.name}</h3>
              <p>{kb.description}</p>
              <div className={styles.stat}>
                <span>{kb.documentCount} 文档</span>
                <span>{kb.imageCount} 图片</span>
              </div>
            </Panel>
          </Link>
        ))}
      </div>
    </div>
  );
}
