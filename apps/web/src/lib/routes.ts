export const routes = {
  login: "/login",
  workspaces: "/workspaces",
  workspaceHome: (workspaceId: string) => `/w/${workspaceId}`,
  chat: (workspaceId: string) => `/w/${workspaceId}/chat`,
  chatConversation: (workspaceId: string, conversationId: string) =>
    `/w/${workspaceId}/chat/${conversationId}`,
  knowledge: (workspaceId: string) => `/w/${workspaceId}/knowledge`,
  knowledgeDetail: (workspaceId: string, kbId: string) =>
    `/w/${workspaceId}/knowledge/${kbId}`,
  assets: (workspaceId: string) => `/w/${workspaceId}/assets`,
  settings: (workspaceId: string) => `/w/${workspaceId}/settings`,
} as const;
