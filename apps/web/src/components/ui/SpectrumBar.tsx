import { cn } from "@/lib/cn";
import styles from "./SpectrumBar.module.css";

export interface SpectrumBarProps {
  className?: string;
  width?: number | string;
}

export default function SpectrumBar({ className, width }: SpectrumBarProps) {
  return (
    <span
      className={cn(styles.bar, className)}
      style={width != null ? { width } : undefined}
      aria-hidden
    />
  );
}
