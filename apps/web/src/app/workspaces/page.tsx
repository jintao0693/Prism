import WorkspacePicker from "@/features/workspace/components/WorkspacePicker";
import { getCurrentTenant, getCurrentUser } from "@/features/auth";
import { listWorkspaces } from "@/features/workspace";

export default async function WorkspacesPage() {
  const [user, tenant, workspaces] = await Promise.all([
    getCurrentUser(),
    getCurrentTenant(),
    listWorkspaces(),
  ]);

  return (
    <WorkspacePicker tenant={tenant} user={user} workspaces={workspaces} />
  );
}
