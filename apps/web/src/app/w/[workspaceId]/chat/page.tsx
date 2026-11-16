import { redirect } from "next/navigation";
import { createConversation, listConversations } from "@/features/chat";
import { routes } from "@/lib/routes";

export default async function ChatIndexPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  let conversations = await listConversations(workspaceId);
  if (conversations.length === 0) {
    const created = await createConversation(workspaceId, "新对话");
    conversations = [created];
  }
  redirect(routes.chatConversation(workspaceId, conversations[0].id));
}
