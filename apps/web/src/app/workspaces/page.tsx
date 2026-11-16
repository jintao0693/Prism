import WorkspacePicker from "@/features/workspace/components/WorkspacePicker";
import { getCurrentTenant, getCurrentUser } from "@/features/auth";
import { listWorkspaces } from "@/features/workspace";
import { withAuthRedirect } from "@/lib/auth-guard";

export default async function WorkspacesPage() {
  const [user, tenant, workspaces] = await withAuthRedirect(() =>
    Promise.all([getCurrentUser(), getCurrentTenant(), listWorkspaces()]),
  );

  return (
    <WorkspacePicker tenant={tenant} user={user} workspaces={workspaces} />
  );
}
