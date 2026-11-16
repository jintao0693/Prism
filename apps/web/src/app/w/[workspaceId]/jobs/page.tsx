import JobsPanel from "@/features/jobs/components/JobsPanel";

export default async function JobsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  return <JobsPanel workspaceId={workspaceId} />;
}
