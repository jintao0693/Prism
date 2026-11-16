import Link from "next/link";
import MediaPreview from "@/components/media/MediaPreview";
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
  const latest = conversations[0];

  return (
    <div className={`page-enter ${styles.wrap}`}>
      <section className={styles.hero}>
        <h2>今天创作什么？</h2>
        <p>一句话出图、改稿或做成预告；需要品牌设定时勾选知识库即可。</p>
        <div className={styles.quickRow}>
          {latest ? (
            <Link
              className={styles.quickPrimary}
              href={routes.chatConversation(workspaceId, latest.id)}
            >
              继续上次对话
            </Link>
          ) : null}
          <Link
            className={latest ? styles.quick : styles.quickPrimary}
            href={routes.chat(workspaceId)}
          >
            {latest ? "新开对话" : "去创作对话"}
          </Link>
          <Link className={styles.quick} href={routes.knowledge(workspaceId)}>
            知识库
          </Link>
          <Link className={styles.quick} href={routes.assets(workspaceId)}>
            资产中心
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
                <span className={styles.rowText}>
                  <strong>{c.title}</strong>
                  <span className={styles.meta}>
                    {c.kind === "video"
                      ? "视频"
                      : c.kind === "image"
                        ? "图片"
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
              <Link
                key={a.id}
                href={`${routes.assets(workspaceId)}?highlight=${encodeURIComponent(a.id)}`}
                className={styles.row}
              >
                <span className={`${styles.thumbBox} thumb-${a.tone}`}>
                  {a.url || a.thumbUrl ? (
                    <MediaPreview
                      url={a.url}
                      thumbUrl={a.thumbUrl}
                      kind={a.kind}
                      previewKind={a.previewKind}
                      mimeType={a.mimeType}
                      alt={a.name}
                      className={styles.thumbMedia}
                      preferThumb
                      controls={false}
                    />
                  ) : null}
                  {a.kind === "video" ? (
                    <span className={styles.thumbBadge}>视频</span>
                  ) : null}
                </span>
                <span className={styles.rowText}>
                  <strong>{a.name}</strong>
                  <span className={styles.meta}>{a.meta}</span>
                </span>
              </Link>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
