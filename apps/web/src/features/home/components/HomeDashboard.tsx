import Link from "next/link";
import Panel from "@/components/ui/Panel";
import { routes } from "@/lib/routes";
import type { AssetItem, ConversationSummary } from "@/types/domain";
import styles from "./HomeDashboard.module.css";

export interface HomeDashboardProps {
  workspaceId: string;
  conversations: ConversationSummary[];
  assets: AssetItem[];
}

export default function HomeDashboard({
  workspaceId,
  conversations,
  assets,
}: HomeDashboardProps) {
  return (
    <div className={`page-enter ${styles.wrap}`}>
      <section className={styles.hero}>
        <h2>今天创作什么？</h2>
        <p>
          用自然语言描述画面或镜头，Prism 会调度生图 / 生视频，并可引用当前空间知识库。
        </p>
        <div className={styles.quickRow}>
          <Link className={styles.quick} href={routes.chat(workspaceId)}>
            生成小红书封面
          </Link>
          <Link className={styles.quick} href={routes.chat(workspaceId)}>
            图生 15 秒种草视频
          </Link>
          <Link className={styles.quick} href={routes.knowledge(workspaceId)}>
            以图搜历史素材
          </Link>
        </div>
      </section>

      <div className={styles.grid}>
        <Panel>
          <div className={styles.sectionTitle}>
            <span>最近对话</span>
            <Link href={routes.chat(workspaceId)}>查看全部</Link>
          </div>
          <div className={styles.list}>
            {conversations.map((c) => (
              <Link
                key={c.id}
                href={routes.chatConversation(workspaceId, c.id)}
                className={styles.row}
              >
                <span className={`thumb-${c.thumbTone} ${styles.thumb}`} />
                <span>
                  <strong>{c.title}</strong>
                  <span className={styles.meta}>
                    {c.kind === "video" ? "生视频" : "生图"} · {c.updatedAtLabel}
                  </span>
                </span>
              </Link>
            ))}
          </div>
        </Panel>

        <Panel>
          <div className={styles.sectionTitle}>
            <span>最近资产</span>
            <Link href={routes.assets(workspaceId)}>资产中心</Link>
          </div>
          <div className={styles.list}>
            {assets.slice(0, 3).map((a) => (
              <div key={a.id} className={styles.row}>
                <span className={`thumb-${a.tone} ${styles.thumb}`} />
                <span>
                  <strong>{a.name}</strong>
                  <span className={styles.meta}>{a.meta}</span>
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
