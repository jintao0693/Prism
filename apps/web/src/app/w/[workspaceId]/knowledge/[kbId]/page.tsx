import KnowledgeDetail from "@/features/knowledge/components/KnowledgeDetail";
import {
  getKnowledgeBase,
  searchByImage,
} from "@/features/knowledge";

export default async function KnowledgeDetailPage({
  params,
}: {
  params: Promise<{ workspaceId: string; kbId: string }>;
}) {
  const { workspaceId, kbId } = await params;
  const [knowledgeBase, initialHits] = await Promise.all([
    getKnowledgeBase(kbId, workspaceId),
    searchByImage(kbId, undefined, workspaceId),
  ]);

  return (
    <KnowledgeDetail
      workspaceId={workspaceId}
      knowledgeBase={knowledgeBase}
      initialHits={initialHits}
    />
  );
}
