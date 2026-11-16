import KnowledgeList from "@/features/knowledge/components/KnowledgeList";
import { listKnowledgeBases } from "@/features/knowledge";

export default async function KnowledgePage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const bases = await listKnowledgeBases(workspaceId);

  return <KnowledgeList workspaceId={workspaceId} bases={bases} />;
}
