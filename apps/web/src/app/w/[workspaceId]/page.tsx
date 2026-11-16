import HomeDashboard from "@/features/home/components/HomeDashboard";
import { listAssets } from "@/features/assets";
import { listConversations } from "@/features/chat";

export default async function WorkspaceHomePage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [conversations, assets] = await Promise.all([
    listConversations(workspaceId),
    listAssets(workspaceId),
  ]);

  return (
    <HomeDashboard
      workspaceId={workspaceId}
      conversations={conversations}
      assets={assets}
    />
  );
}
