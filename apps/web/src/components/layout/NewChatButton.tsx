"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import { createConversation } from "@/features/chat";
import { routes } from "@/lib/routes";

export default function NewChatButton({ workspaceId }: { workspaceId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function handleClick() {
    if (busy) return;
    setBusy(true);
    try {
      const created = await createConversation(workspaceId, "新对话");
      router.push(routes.chatConversation(workspaceId, created.id));
      router.refresh();
    } catch {
      router.push(routes.chat(workspaceId));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Button variant="ghost" onClick={() => void handleClick()} disabled={busy}>
      {busy ? "创建中…" : "＋ 新对话"}
    </Button>
  );
}
