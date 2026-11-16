"use client";

import { useEffect } from "react";
import { loadStoredAuth } from "@/features/auth";
import { setRequestContext } from "@/lib/api-client";

export interface WorkspaceContextBridgeProps {
  workspaceId: string;
}

/** 进入工作空间后注入 X-Workspace-Id / Token。 */
export default function WorkspaceContextBridge({
  workspaceId,
}: WorkspaceContextBridgeProps) {
  useEffect(() => {
    loadStoredAuth();
    setRequestContext({ workspaceId });
  }, [workspaceId]);

  return null;
}
