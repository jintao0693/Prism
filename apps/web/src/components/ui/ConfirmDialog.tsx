"use client";

import { useEffect, useRef, type ReactNode } from "react";
import Button from "@/components/ui/Button";
import styles from "./ConfirmDialog.module.css";

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  secondaryLabel?: string;
  danger?: boolean;
  inputValue?: string;
  inputPlaceholder?: string;
  onInputChange?: (value: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
  onSecondary?: () => void;
}

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "确定",
  cancelLabel = "取消",
  secondaryLabel,
  danger,
  inputValue,
  inputPlaceholder,
  onInputChange,
  onConfirm,
  onCancel,
  onSecondary,
}: ConfirmDialogProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKey);
    if (onInputChange) {
      window.setTimeout(() => inputRef.current?.focus(), 0);
    }
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel, onInputChange]);

  if (!open) return null;

  return (
    <div className={styles.backdrop} role="presentation" onClick={onCancel}>
      <div
        className={styles.panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="prism-dialog-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="prism-dialog-title">{title}</h3>
        {description ? <div className={styles.desc}>{description}</div> : null}
        {onInputChange ? (
          <input
            ref={inputRef}
            className={styles.input}
            value={inputValue ?? ""}
            placeholder={inputPlaceholder}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onConfirm();
            }}
          />
        ) : null}
        <div className={styles.actions}>
          <Button variant="ghost" type="button" onClick={onCancel}>
            {cancelLabel}
          </Button>
          {secondaryLabel && onSecondary ? (
            <Button variant="ghost" type="button" onClick={onSecondary}>
              {secondaryLabel}
            </Button>
          ) : null}
          <Button
            type="button"
            className={danger ? styles.danger : undefined}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
