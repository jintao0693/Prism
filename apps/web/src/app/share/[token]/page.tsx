import MediaPreview from "@/components/media/MediaPreview";
import Panel from "@/components/ui/Panel";
import { getPublicShare } from "@/features/shares/api/sharesApi";
import styles from "./page.module.css";

export default async function SharePage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  let data;
  let err: string | null = null;
  try {
    data = await getPublicShare(token);
  } catch (e) {
    err = e instanceof Error ? e.message : "分享无法打开";
  }

  if (err || !data) {
    return (
      <main className={styles.wrap}>
        <Panel>
          <h1>分享不可用</h1>
          <p>{err || "链接无效或已过期"}</p>
        </Panel>
      </main>
    );
  }

  const kind = data.kind === "video" ? "video" : "image";

  return (
    <main className={styles.wrap}>
      <Panel className={styles.card}>
        <p className={styles.eyebrow}>Prism 只读分享</p>
        <h1>{data.title}</h1>
        {data.note ? <p className={styles.note}>{data.note}</p> : null}
        {data.url || data.thumbUrl ? (
          <div className={styles.media}>
            <MediaPreview
              url={data.url}
              thumbUrl={data.thumbUrl}
              kind={kind}
              previewKind={data.previewKind}
              mimeType={data.mimeType}
              alt={data.title}
              className={styles.preview}
              preferThumb={false}
            />
          </div>
        ) : (
          <p className={styles.note}>资源暂无可预览文件。</p>
        )}
      </Panel>
    </main>
  );
}