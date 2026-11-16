"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/cn";
import MediaPreview from "@/components/media/MediaPreview";
import MediaLightbox from "@/components/media/MediaLightbox";
import type { ChatMessage, GenerationResult } from "@/types/domain";
import styles from "./MessageBubble.module.css";

export interface MessageBubbleProps {
  message: ChatMessage;
  onRetry?: () => void;
}

export default function MessageBubble({ message, onRetry }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const hasText = Boolean(message.content?.trim());
  const hasResults = Boolean(message.results?.length);
  const [preview, setPreview] = useState<GenerationResult | null>(null);

  const byId = useMemo(() => {
    const map = new Map<string, GenerationResult>();
    for (const r of message.results || []) map.set(r.id, r);
    return map;
  }, [message.results]);

  function lineageOf(r: GenerationResult): string | null {
    if (!r.parentAssetId) return null;
    const parent = byId.get(r.parentAssetId);
    if (parent) return `基于「${parent.label}」改稿`;
    return `基于资产 ${r.parentAssetId.slice(0, 10)}… 改稿`;
  }

  return (
    <div
      className={cn(
        styles.bubble,
        isUser ? styles.user : styles.agent,
        message.streaming && styles.streaming,
        message.failed && styles.failed,
      )}
    >
      {hasText ? (
        <p>
          {message.content}
          {message.streaming ? (
            <span className={styles.caret} aria-hidden />
          ) : null}
        </p>
      ) : message.streaming ? (
        <p className={styles.pending}>
          正在生成…
          <span className={styles.caret} aria-hidden />
        </p>
      ) : null}
      {message.failed ? (
        <div className={styles.failRow}>
          <span>发送未成功，内容已保留</span>
          {onRetry ? (
            <button type="button" className={styles.retryBtn} onClick={onRetry}>
              重试
            </button>
          ) : null}
        </div>
      ) : null}
      {message.toolLabel ? (
        <span className={styles.tool}>✦ {message.toolLabel}</span>
      ) : null}
      {hasResults ? (
        <div className={styles.results}>
          {message.results!.map((r) => {
            const lineage = lineageOf(r);
            return (
              <button
                key={r.id}
                type="button"
                className={cn(
                  styles.result,
                  !r.url && !r.thumbUrl && `thumb-${r.tone}`,
                )}
                onClick={() => {
                  if (r.url || r.thumbUrl) setPreview(r);
                }}
              >
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
                    controls={false}
                  />
                ) : null}
                <span>{r.label}</span>
                {lineage ? (
                  <em className={styles.lineageBadge}>{lineage}</em>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}

      <MediaLightbox
        open={Boolean(preview)}
        onClose={() => setPreview(null)}
        url={preview?.url}
        thumbUrl={preview?.thumbUrl}
        kind={preview?.kind}
        previewKind={preview?.previewKind}
        mimeType={preview?.mimeType}
        title={preview?.label}
        lineageLabel={preview ? lineageOf(preview) : null}
      />
    </div>
  );
}
