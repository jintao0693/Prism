export const routes = {
  login: "/login",
  workspaces: "/workspaces",
  workspaceHome: (workspaceId: string) => `/w/${workspaceId}`,
  chat: (workspaceId: string) => `/w/${workspaceId}/chat`,
  chatConversation: (
    workspaceId: string,
    conversationId: string,
    opts?: { referenceAssetIds?: string[] },
  ) => {
    const base = `/w/${workspaceId}/chat/${conversationId}`;
    const ids = opts?.referenceAssetIds?.filter(Boolean) ?? [];
    if (!ids.length) return base;
    return `${base}?referenceAssetIds=${encodeURIComponent(ids.join(","))}`;
  },
  knowledge: (workspaceId: string) => `/w/${workspaceId}/knowledge`,
  knowledgeDetail: (workspaceId: string, kbId: string) =>
    `/w/${workspaceId}/knowledge/${kbId}`,
  assets: (workspaceId: string) => `/w/${workspaceId}/assets`,
  jobs: (workspaceId: string) => `/w/${workspaceId}/jobs`,
  settings: (workspaceId: string) => `/w/${workspaceId}/settings`,
  share: (token: string) => `/share/${token}`,
  cases: "/cases",
} as const;
