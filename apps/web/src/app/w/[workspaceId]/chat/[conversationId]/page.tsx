import { Suspense } from "react";
import ChatWorkspace from "@/features/chat/components/ChatWorkspace";
import { listConversations } from "@/features/chat";

export default async function ConversationPage({
  params,
}: {
  params: Promise<{ workspaceId: string; conversationId: string }>;
}) {
  const { workspaceId, conversationId } = await params;
  const conversations = await listConversations(workspaceId);

  return (
    <Suspense fallback={<p style={{ padding: 24 }}>加载对话…</p>}>
      <ChatWorkspace
        workspaceId={workspaceId}
        conversations={conversations}
        activeConversationId={conversationId}
      />
    </Suspense>
  );
}
