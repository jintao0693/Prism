import ChatWorkspace from "@/features/chat/components/ChatWorkspace";
import { listConversations } from "@/features/chat";

export default async function ChatConversationPage({
  params,
}: {
  params: Promise<{ workspaceId: string; conversationId: string }>;
}) {
  const { workspaceId, conversationId } = await params;
  const conversations = await listConversations(workspaceId);

  return (
    <ChatWorkspace
      workspaceId={workspaceId}
      conversations={conversations}
      activeConversationId={conversationId}
    />
  );
}
