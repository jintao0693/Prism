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
          对话里直接描述需求：Prism 会自动识别意图，走文本问答、生图或生视频。
          知识库目前支持文本检索 / 以文搜图；上传文件与真·以图搜图还在补。
        </p>
        <div className={styles.quickRow}>
          <Link className={styles.quick} href={routes.chat(workspaceId)}>
            去创作对话
          </Link>
          <Link className={styles.quick} href={routes.knowledge(workspaceId)}>
            打开知识库检索
          </Link>
          <Link className={styles.quick} href={routes.assets(workspaceId)}>
            查看资产中心
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
            {conversations.length === 0 ? (
              <p className={styles.empty}>还没有对话，去创作一句话试试。</p>
            ) : null}
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
                    {c.kind === "video"
                      ? "视频会话"
                      : c.kind === "image"
                        ? "图片会话"
                        : "对话"}{" "}
                    · {c.updatedAtLabel}
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
            {assets.length === 0 ? (
              <p className={styles.empty}>生成图/视频后会出现在这里。</p>
            ) : null}
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
