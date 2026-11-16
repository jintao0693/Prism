import { redirect } from "next/navigation";
import { listConversations } from "@/features/chat";
import { routes } from "@/lib/routes";

export default async function ChatIndexPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const conversations = await listConversations(workspaceId);
  const first = conversations[0];
  if (!first) {
    redirect(routes.workspaceHome(workspaceId));
  }
  redirect(routes.chatConversation(workspaceId, first.id));
}
