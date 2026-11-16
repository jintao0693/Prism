import { cn } from "@/lib/cn";
import MediaPreview from "@/components/media/MediaPreview";
import type { ChatMessage } from "@/types/domain";
import styles from "./MessageBubble.module.css";

export interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const hasText = Boolean(message.content?.trim());
  const hasResults = Boolean(message.results?.length);

  return (
    <div
      className={cn(
        styles.bubble,
        isUser ? styles.user : styles.agent,
        message.streaming && styles.streaming,
      )}
    >
      {hasText ? (
        <p>
          {message.content}
          {message.streaming ? <span className={styles.caret} aria-hidden /> : null}
        </p>
      ) : message.streaming ? (
        <p className={styles.pending}>
          正在生成…
          <span className={styles.caret} aria-hidden />
        </p>
      ) : null}
      {message.toolLabel ? (
        <span className={styles.tool}>✦ {message.toolLabel}</span>
      ) : null}
      {hasResults ? (
        <div className={styles.results}>
          {message.results!.map((r) => (
            <div key={r.id} className={cn(styles.result, !r.url && !r.thumbUrl && `thumb-${r.tone}`)}>
              {r.url || r.thumbUrl ? (
                <MediaPreview
                  url={r.url}
                  thumbUrl={r.thumbUrl}
                  kind={r.kind}
                  previewKind={r.previewKind}
                  mimeType={r.mimeType}
                  alt={r.label}
                  className={styles.resultImg}
                  preferThumb={r.kind !== "video"}
                  controls={r.kind === "video" && r.previewKind !== "poster"}
                />
              ) : null}
              <span>{r.label}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
