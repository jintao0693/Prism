import Link from "next/link";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import type { Workspace } from "@/types/domain";
import styles from "./WorkspaceCard.module.css";

export interface WorkspaceCardProps {
  workspace: Workspace;
}

export default function WorkspaceCard({ workspace }: WorkspaceCardProps) {
  const evergreen = workspace.status === "evergreen";

  return (
    <Link
      href={routes.workspaceHome(workspace.id)}
      className={styles.card}
    >
      <span className={cn(styles.tag, evergreen && styles.evergreen)}>
        {evergreen ? "常青" : "进行中"}
      </span>
      <h3>{workspace.name}</h3>
      <p>{workspace.description}</p>
      <div className={styles.meta}>
        {workspace.conversationCount} 个对话 · {workspace.assetCount} 个资产 ·{" "}
        {workspace.updatedAtLabel}
      </div>
    </Link>
  );
}
