"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
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
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  function handleCreate() {
    const title = name.trim() || "未命名知识库";
    setError(null);
    setCreating(false);
    startTransition(() => {
      void createKnowledgeBase(
        workspaceId,
        title,
        "当前工作空间素材与文档",
      )
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
        description="沉淀品牌设定与素材，对话里勾选后即可引用；支持文字检索与图搜。"
        actions={
          <Button
            onClick={() => {
              setName("");
              setCreating(true);
            }}
            disabled={pending}
          >
            {pending ? "创建中…" : "新建知识库"}
          </Button>
        }
      />
      {error ? <p className={styles.error}>{error}</p> : null}
      <div className={styles.grid}>
        {bases.length === 0 ? (
          <Panel className={styles.empty}>
            <h3>还没有知识库</h3>
            <p>
              先新建一个，再上传图片或写入文档，即可在对话里引用资料问答与搜图。
            </p>
          </Panel>
        ) : null}
        {bases.map((kb) => (
          <Link
            key={kb.id}
            href={routes.knowledgeDetail(workspaceId, kb.id)}
            className={styles.cardLink}
          >
            <Panel className={styles.card}>
              <SpectrumBar />
              <h3>{kb.name}</h3>
              <p>{kb.description || "暂无描述"}</p>
              <span className={styles.stat}>
                <span>{kb.documentCount} 文档</span>
                <span>{kb.imageCount} 图片</span>
              </span>
            </Panel>
          </Link>
        ))}
      </div>

      <ConfirmDialog
        open={creating}
        title="新建知识库"
        description="起个好认的名字，例如「品牌视觉规范」或「活动素材库」。"
        confirmLabel="创建"
        inputValue={name}
        inputPlaceholder="知识库名称"
        onInputChange={setName}
        onCancel={() => setCreating(false)}
        onConfirm={handleCreate}
      />
    </div>
  );
}
