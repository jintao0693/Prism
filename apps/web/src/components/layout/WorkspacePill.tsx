import Link from "next/link";
import styles from "./WorkspacePill.module.css";

export interface WorkspacePillProps {
  name: string;
  href: string;
}

export default function WorkspacePill({ name, href }: WorkspacePillProps) {
  return (
    <Link href={href} className={styles.pill} title="切换工作空间">
      <span className={styles.dot} aria-hidden />
      <span>{name}</span>
      <span className={styles.caret} aria-hidden>
        ▾
      </span>
    </Link>
  );
}
