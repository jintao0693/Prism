"use client";

import { useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import styles from "./ChatComposer.module.css";

export interface ChatComposerProps {
  disabled?: boolean;
  onSend: (text: string) => Promise<void> | void;
}

export default function ChatComposer({ disabled, onSend }: ChatComposerProps) {
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
          placeholder="描述画面、镜头或直接提问…"
          rows={3}
          disabled={sending || disabled}
        />
        <div className={styles.bar}>
          <div className={styles.chips}>
            <span className={styles.chip}>文生图</span>
            <span className={styles.chip}>图生视频</span>
            <span className={styles.chip}>文本问答</span>
          </div>
          <Button type="submit" disabled={sending || !value.trim()}>
            {sending ? "发送中…" : "发送"}
          </Button>
        </div>
      </div>
    </form>
  );
}
