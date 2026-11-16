"use client";

import { useEffect } from "react";
import MediaPreview from "@/components/media/MediaPreview";
import type { MediaPreviewKind } from "@/components/media/MediaPreview";
import styles from "./MediaLightbox.module.css";

export interface MediaLightboxProps {
  open: boolean;
  onClose: () => void;
  url?: string;
  thumbUrl?: string;
  kind?: "image" | "video";
  previewKind?: MediaPreviewKind;
  mimeType?: string;
  title?: string;
  lineageLabel?: string | null;
}

export default function MediaLightbox({
  open,
  onClose,
  url,
  thumbUrl,
  kind,
  previewKind,
  mimeType,
  title,
  lineageLabel,
}: MediaLightboxProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open || (!url && !thumbUrl)) return null;

  const downloadHref = url || thumbUrl || "";

  return (
    <div
      className={styles.backdrop}
      role="dialog"
      aria-modal="true"
      aria-label={title || "预览"}
      onClick={onClose}
    >
      <div
        className={styles.panel}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.toolbar}>
          <div className={styles.meta}>
            <strong>{title || "预览"}</strong>
            {lineageLabel ? (
              <span className={styles.lineage}>{lineageLabel}</span>
            ) : null}
          </div>
          <div className={styles.actions}>
            {downloadHref ? (
              <a
                className={styles.btn}
                href={downloadHref}
                download
                target="_blank"
                rel="noreferrer"
              >
                下载
              </a>
            ) : null}
            <button type="button" className={styles.btn} onClick={onClose}>
              关闭
            </button>
          </div>
        </div>
        <div className={styles.stage}>
          <MediaPreview
            url={url}
            thumbUrl={thumbUrl}
            kind={kind}
            previewKind={previewKind}
            mimeType={mimeType}
            alt={title || "预览"}
            className={styles.media}
            preferThumb={false}
            controls={kind === "video" || previewKind === "video"}
          />
        </div>
      </div>
    </div>
  );
}
