import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import styles from "./Panel.module.css";

export interface PanelProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export default function Panel({ className, children, ...rest }: PanelProps) {
  return (
    <div className={cn(styles.panel, className)} {...rest}>
      {children}
    </div>
  );
}
