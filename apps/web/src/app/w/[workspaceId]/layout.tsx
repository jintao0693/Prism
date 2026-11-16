import AppShell from "@/components/layout/AppShell";
import WorkspaceContextBridge from "@/components/layout/WorkspaceContextBridge";
import { getCurrentUser } from "@/features/auth";
import { getUsageSummary, getWorkspace } from "@/features/workspace";

export default async function WorkspaceLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [user, workspace, usage] = await Promise.all([
    getCurrentUser(),
    getWorkspace(workspaceId),
    getUsageSummary(),
  ]);

  return (
    <AppShell
      workspaceId={workspaceId}
      workspaceName={workspace.name}
      userName={user.name}
      avatarText={user.avatarText}
      usage={usage}
    >
      <WorkspaceContextBridge workspaceId={workspaceId} />
      {children}
    </AppShell>
  );
}
