import KnowledgeDetail from "@/features/knowledge/components/KnowledgeDetail";
import { getKnowledgeBase } from "@/features/knowledge";

export default async function KnowledgeDetailPage({
  params,
}: {
  params: Promise<{ workspaceId: string; kbId: string }>;
}) {
  const { workspaceId, kbId } = await params;
  const knowledgeBase = await getKnowledgeBase(kbId, workspaceId);

  return (
    <KnowledgeDetail
      workspaceId={workspaceId}
      knowledgeBase={knowledgeBase}
      initialHits={[]}
    />
  );
}
