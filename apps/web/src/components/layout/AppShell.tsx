import type { ReactNode } from "react";
import Topbar from "@/components/layout/Topbar";
import Sidebar from "@/components/layout/Sidebar";
import type { UsageSummary } from "@/types/domain";
import styles from "./AppShell.module.css";

export interface AppShellProps {
  workspaceId: string;
  workspaceName: string;
  userName: string;
  avatarText: string;
  usage: UsageSummary;
  children: ReactNode;
}

export default function AppShell({
  workspaceId,
  workspaceName,
  userName,
  avatarText,
  usage,
  children,
}: AppShellProps) {
  return (
    <div className={styles.app}>
      <Topbar
        workspaceId={workspaceId}
        workspaceName={workspaceName}
        userName={userName}
        avatarText={avatarText}
      />
      <div className={styles.shell}>
        <Sidebar workspaceId={workspaceId} usage={usage} />
        <main className={styles.main}>{children}</main>
      </div>
    </div>
  );
}
