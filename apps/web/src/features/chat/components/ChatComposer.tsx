"use client";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import Button from "@/components/ui/Button";
import styles from "./ChatComposer.module.css";

const PROMPT_TEMPLATES = [
  { label: "生图示例", text: "画一张春季大促主视觉海报，青石色主调，干净留白" },
  { label: "参考改图", text: "按参考图再偏暖一点，保留构图与人物位置" },
  { label: "图生视频", text: "把这张做成 5 秒氛围预告：镜头缓慢推进" },
  { label: "问答示例", text: "用一句话介绍 Prism 能做什么" },
] as const;

export type ComposerAttachment = {
  file: File;
  previewUrl: string;
};

export type ComposerKbOption = {
  id: string;
  name: string;
};

export type ComposerPendingRef = {
  id: string;
  name: string;
  thumbUrl?: string;
  url?: string;
};

export interface ChatComposerProps {
  disabled?: boolean;
  statusText?: string | null;
  quotaHint?: string | null;
  /** 外部注入草稿（失败重试 / 知识库带回） */
  draftText?: string | null;
  draftNonce?: number;
  onSend: (text: string, attachments: File[]) => Promise<void> | void;
  knowledgeBases?: ComposerKbOption[];
  selectedKbIds?: string[];
  onToggleKb?: (id: string) => void;
  pendingRefs?: ComposerPendingRef[];
  onRemovePendingRef?: (id: string) => void;
  kbEmptyHint?: ReactNode;
}

export default function ChatComposer({
  disabled,
  statusText,
  quotaHint,
  draftText,
  draftNonce = 0,
  onSend,
  knowledgeBases = [],
  selectedKbIds = [],
  onToggleKb,
  pendingRefs = [],
  onRemovePendingRef,
  kbEmptyHint,
}: ChatComposerProps) {
  const [value, setValue] = useState("");
  const [sending, setSending] = useState(false);
  const [attachments, setAttachments] = useState<ComposerAttachment[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (draftNonce > 0 && draftText != null) {
      setValue(draftText);
    }
  }, [draftNonce, draftText]);

  function clearAttachments() {
    setAttachments((prev) => {
      for (const item of prev) URL.revokeObjectURL(item.previewUrl);
      return [];
    });
  }

  function onPickFiles(files: FileList | null) {
    if (!files?.length) return;
    const next: ComposerAttachment[] = [];
    for (const file of Array.from(files).slice(0, 2)) {
      if (!file.type.startsWith("image/")) continue;
      next.push({ file, previewUrl: URL.createObjectURL(file) });
    }
    if (!next.length) return;
    setAttachments((prev) => {
      for (const item of prev) URL.revokeObjectURL(item.previewUrl);
      return next;
    });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const text = value.trim();
    if ((!text && attachments.length === 0) || sending || disabled) {
      return;
    }
    const payloadText =
      text ||
      (attachments.length
        ? "请基于参考图继续创作（可改色调 / 做成预告）。"
        : "");
    if (!payloadText) return;
    setSending(true);
    try {
      await onSend(
        payloadText,
        attachments.map((a) => a.file),
      );
      setValue("");
      clearAttachments();
    } finally {
      setSending(false);
    }
  }

  const busy = sending || disabled;
  const selectedCount = selectedKbIds.length;

  return (
    <form className={styles.composer} onSubmit={handleSubmit}>
      {pendingRefs.length > 0 ? (
        <div className={styles.refRow}>
          <span className={styles.metaLabel}>待发送参考图</span>
          {pendingRefs.map((ref) => (
            <div key={ref.id} className={styles.refChip}>
              {ref.thumbUrl || ref.url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={ref.thumbUrl || ref.url} alt={ref.name} />
              ) : null}
              <span>{ref.name}</span>
              <button
                type="button"
                disabled={busy}
                onClick={() => onRemovePendingRef?.(ref.id)}
              >
                移除
              </button>
            </div>
          ))}
        </div>
      ) : null}

      <div className={styles.box}>
        {attachments.length > 0 ? (
          <div className={styles.previews}>
            {attachments.map((item) => (
              <div key={item.previewUrl} className={styles.preview}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={item.previewUrl} alt={item.file.name} />
                <button
                  type="button"
                  className={styles.remove}
                  disabled={busy}
                  onClick={() => {
                    URL.revokeObjectURL(item.previewUrl);
                    setAttachments((prev) =>
                      prev.filter((x) => x.previewUrl !== item.previewUrl),
                    );
                  }}
                >
                  移除
                </button>
              </div>
            ))}
          </div>
        ) : null}
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="直接提问，或附参考图后说「再偏暖 / 做成预告」…"
          rows={3}
          disabled={busy}
        />
        <div className={styles.bar}>
          <div className={styles.chips}>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              hidden
              onChange={(e) => {
                onPickFiles(e.target.files);
                e.target.value = "";
              }}
            />
            <button
              type="button"
              className={styles.chip}
              disabled={busy}
              onClick={() => fileRef.current?.click()}
            >
              附参考图
            </button>
            {PROMPT_TEMPLATES.map((item) => (
              <button
                key={item.label}
                type="button"
                className={styles.chip}
                disabled={busy}
                onClick={() => setValue(item.text)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <Button
            type="submit"
            disabled={busy || (!value.trim() && attachments.length === 0)}
          >
            {sending ? "发送中…" : "发送"}
          </Button>
        </div>
        {statusText ? <p className={styles.status}>{statusText}</p> : null}
        {quotaHint ? <p className={styles.quotaHint}>{quotaHint}</p> : null}
      </div>

      <div className={styles.kbRow}>
        <span className={styles.metaLabel}>
          引用知识库
          {selectedCount > 0 ? (
            <em className={styles.kbCount}>已选 {selectedCount}</em>
          ) : null}
        </span>
        {knowledgeBases.length === 0 ? (
          <span className={styles.kbEmpty}>
            {kbEmptyHint ?? "当前空间暂无知识库"}
          </span>
        ) : (
          knowledgeBases.map((kb) => {
            const on = selectedKbIds.includes(kb.id);
            return (
              <button
                key={kb.id}
                type="button"
                className={on ? styles.kbPillOn : styles.kbPill}
                disabled={busy || !onToggleKb}
                aria-pressed={on}
                onClick={() => onToggleKb?.(kb.id)}
                title={kb.name}
              >
                {kb.name}
              </button>
            );
          })
        )}
      </div>
      <p className={styles.hint}>
        勾选知识库后可走资料问答；生图约数十秒，视频约 1–3 分钟。
      </p>
    </form>
  );
}
