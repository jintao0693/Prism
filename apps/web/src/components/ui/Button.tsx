import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import styles from "./Button.module.css";

export type ButtonVariant = "primary" | "ghost";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
}

export default function Button({
  variant = "primary",
  className,
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(styles.btn, styles[variant], className)}
      {...rest}
    >
      {children}
    </button>
  );
}
