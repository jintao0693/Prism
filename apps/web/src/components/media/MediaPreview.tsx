"use client";

import { cn } from "@/lib/cn";
import styles from "./MediaPreview.module.css";

export type MediaPreviewKind = "image" | "video" | "poster";

export interface MediaPreviewProps {
  url?: string;
  thumbUrl?: string;
  kind?: "image" | "video";
  previewKind?: MediaPreviewKind;
  mimeType?: string;
  alt?: string;
  className?: string;
  /** 画廊用缩略图优先；对话结果可点看原片 */
  preferThumb?: boolean;
  controls?: boolean;
}

function inferPreviewKind(
  url?: string,
  kind?: string,
  previewKind?: MediaPreviewKind,
  mimeType?: string,
): MediaPreviewKind {
  if (previewKind === "image" || previewKind === "video" || previewKind === "poster") {
    return previewKind;
  }
  const mime = (mimeType || "").toLowerCase();
  const path = (url || "").toLowerCase();
  const looksImage =
    mime.startsWith("image/") ||
    /\.(png|jpe?g|webp|gif)(\?|$)/i.test(path);
  const looksVideo =
    mime.startsWith("video/") || /\.(mp4|webm|mov)(\?|$)/i.test(path);
  if (kind === "video" && looksImage && !looksVideo) return "poster";
  if (looksVideo || kind === "video") return "video";
  return "image";
}

export default function MediaPreview({
  url,
  thumbUrl,
  kind,
  previewKind,
  mimeType,
  alt = "预览",
  className,
  preferThumb = true,
  controls = false,
}: MediaPreviewProps) {
  const mode = inferPreviewKind(url, kind, previewKind, mimeType);
  const displayUrl =
    preferThumb && mode !== "video"
      ? thumbUrl || url
      : url || thumbUrl;

  if (!displayUrl) {
    return <div className={cn(styles.fallback, className)} aria-hidden />;
  }

  if (mode === "video") {
    return (
      <video
        className={cn(styles.media, className)}
        src={url || displayUrl}
        poster={thumbUrl}
        muted
        playsInline
        controls={controls}
        preload="metadata"
      />
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={displayUrl}
      alt={alt}
      className={cn(styles.media, className)}
      loading="lazy"
      decoding="async"
    />
  );
}
