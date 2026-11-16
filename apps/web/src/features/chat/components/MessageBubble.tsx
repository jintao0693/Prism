import { cn } from "@/lib/cn";
import type { ChatMessage } from "@/types/domain";
import styles from "./MessageBubble.module.css";

export interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn(styles.bubble, isUser ? styles.user : styles.agent)}>
      <p>{message.content}</p>
      {message.toolLabel ? (
        <span className={styles.tool}>✦ {message.toolLabel}</span>
      ) : null}
      {message.results && message.results.length > 0 ? (
        <div className={styles.results}>
          {message.results.map((r) => (
            <div key={r.id} className={cn(styles.result, !r.url && `thumb-${r.tone}`)}>
              {r.url && r.kind !== "video" ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={r.url} alt={r.label} className={styles.resultImg} />
              ) : null}
              {r.url && r.kind === "video" ? (
                <video
                  className={styles.resultImg}
                  src={r.url}
                  muted
                  playsInline
                  preload="metadata"
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
