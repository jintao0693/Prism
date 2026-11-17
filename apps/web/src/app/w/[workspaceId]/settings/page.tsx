import SettingsPanel from "@/features/settings/components/SettingsPanel";

export default async function SettingsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  return <SettingsPanel workspaceId={workspaceId} />;
}
