"use client";

import { useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import styles from "./ChatComposer.module.css";

const PROMPT_TEMPLATES = [
  { label: "生图示例", text: "画一张春季大促主视觉海报，青石色主调，干净留白" },
  { label: "生视频示例", text: "做一条 15 秒种草短视频，竖屏，产品瓶身慢推" },
  { label: "问答示例", text: "用一句话介绍 Prism 能做什么" },
] as const;

export interface ChatComposerProps {
  disabled?: boolean;
  statusText?: string | null;
  onSend: (text: string) => Promise<void> | void;
}

export default function ChatComposer({
  disabled,
  statusText,
  onSend,
}: ChatComposerProps) {
  const [value, setValue] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const text = value.trim();
    if (!text || sending || disabled) {
      return;
    }
    setSending(true);
    try {
      await onSend(text);
      setValue("");
    } finally {
      setSending(false);
    }
  }

  return (
    <form className={styles.composer} onSubmit={handleSubmit}>
      <div className={styles.box}>
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="直接提问，或描述要生成的图/视频…（意图由模型自动识别）"
          rows={3}
          disabled={sending || disabled}
        />
        <div className={styles.bar}>
          <div className={styles.chips}>
            {PROMPT_TEMPLATES.map((item) => (
              <button
                key={item.label}
                type="button"
                className={styles.chip}
                disabled={sending || disabled}
                onClick={() => setValue(item.text)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <Button type="submit" disabled={sending || disabled || !value.trim()}>
            {sending ? "发送中…" : "发送"}
          </Button>
        </div>
        {statusText ? <p className={styles.status}>{statusText}</p> : null}
        <p className={styles.hint}>
          能力说明：文本问答 / 生图 / 生视频会自动路由；勾选知识库后可走资料问答。
        </p>
      </div>
    </form>
  );
}
