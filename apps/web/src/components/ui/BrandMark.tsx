import { cn } from "@/lib/cn";
import styles from "./BrandMark.module.css";

export interface BrandMarkProps {
  className?: string;
  showName?: boolean;
}

export default function BrandMark({
  className,
  showName = true,
}: BrandMarkProps) {
  return (
    <div className={cn(styles.brand, className)}>
      <span className={styles.mark} aria-hidden />
      {showName ? <span className={styles.name}>Prism</span> : null}
    </div>
  );
}
