"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import { createConversation } from "@/features/chat";
import { routes } from "@/lib/routes";

export default function NewChatButton({ workspaceId }: { workspaceId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createConversation(workspaceId, "新对话");
      router.push(routes.chatConversation(workspaceId, created.id));
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "创建对话失败，请重试");
    } finally {
      setBusy(false);
    }
  }

  return (
    <span style={{ display: "inline-flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
      <Button variant="ghost" onClick={() => void handleClick()} disabled={busy}>
        {busy ? "创建中…" : "＋ 新对话"}
      </Button>
      {error ? (
        <span role="alert" style={{ fontSize: 11, color: "#b42318", maxWidth: 160 }}>
          {error}
        </span>
      ) : null}
    </span>
  );
}
