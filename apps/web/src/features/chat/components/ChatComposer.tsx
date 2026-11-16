"use client";

import { useRef, useState, type FormEvent } from "react";
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

export interface ChatComposerProps {
  disabled?: boolean;
  statusText?: string | null;
  onSend: (text: string, attachments: File[]) => Promise<void> | void;
}

export default function ChatComposer({
  disabled,
  statusText,
  onSend,
}: ChatComposerProps) {
  const [value, setValue] = useState("");
  const [sending, setSending] = useState(false);
  const [attachments, setAttachments] = useState<ComposerAttachment[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

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

  return (
    <form className={styles.composer} onSubmit={handleSubmit}>
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
        <p className={styles.hint}>
          可上传参考图做图生图 / 图生视频；勾选知识库后可走资料问答。失败时会显示可读错误，不会假装成功。
        </p>
      </div>
    </form>
  );
}
