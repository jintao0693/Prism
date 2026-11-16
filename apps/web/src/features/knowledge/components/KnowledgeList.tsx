import Link from "next/link";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import Panel from "@/components/ui/Panel";
import SpectrumBar from "@/components/ui/SpectrumBar";
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
  return (
    <div className="page-enter">
      <PageHeader
        title="知识库"
        description="文档问答与以图搜图 · 视频片段检索即将推出"
        actions={<Button disabled>新建知识库</Button>}
      />
      <div className={styles.grid}>
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
        <div className={styles.create}>
          <div className={styles.plus}>＋</div>
          <h3>新建知识库</h3>
          <p>为当前工作空间沉淀可检索素材。</p>
        </div>
      </div>
    </div>
  );
}
