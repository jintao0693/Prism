"use client";

import Link from "next/link";
import BrandMark from "@/components/ui/BrandMark";
import Avatar from "@/components/ui/Avatar";
import Button from "@/components/ui/Button";
import WorkspacePill from "@/components/layout/WorkspacePill";
import { routes } from "@/lib/routes";
import styles from "./Topbar.module.css";

export interface TopbarProps {
  workspaceId: string;
  workspaceName: string;
  userName: string;
  avatarText: string;
}

export default function Topbar({
  workspaceId,
  workspaceName,
  userName,
  avatarText,
}: TopbarProps) {
  return (
    <header className={styles.topbar}>
      <div className={styles.left}>
        <Link href={routes.workspaces} className={styles.brandLink}>
          <BrandMark />
        </Link>
        <WorkspacePill
          name={workspaceName}
          href={routes.workspaces}
        />
      </div>
      <div className={styles.right}>
        <Link href={routes.chat(workspaceId)}>
          <Button variant="ghost">＋ 新对话</Button>
        </Link>
        <Avatar text={avatarText} />
        <span className="sr-only">{userName}</span>
      </div>
    </header>
  );
}
