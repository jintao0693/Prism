/** 领域类型：前后端契约雏形，后端就绪后可对齐 OpenAPI */

export type Role = "owner" | "admin" | "creator" | "viewer";

export interface User {
  id: string;
  name: string;
  email: string;
  avatarText: string;
  role: Role;
}

export interface Tenant {
  id: string;
  name: string;
}

export interface Workspace {
  id: string;
  name: string;
  description: string;
  status: "active" | "evergreen";
  conversationCount: number;
  assetCount: number;
  updatedAtLabel: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  kind: "image" | "video" | "chat";
  updatedAtLabel: string;
  thumbTone: "a" | "b" | "c";
}

export type MessageRole = "user" | "assistant";

export interface GenerationResult {
  id: string;
  label: string;
  tone: "a" | "b" | "c" | "d" | "e" | "f";
  kind?: "image" | "video";
  url?: string;
  parentAssetId?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  toolLabel?: string;
  results?: GenerationResult[];
  createdAt: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  documentCount: number;
  imageCount: number;
}

export interface KnowledgeHit {
  id: string;
  title: string;
  summary: string;
  score: number;
  tone: "a" | "b" | "c" | "d" | "e" | "f";
  itemType?: "document" | "image";
  url?: string;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  itemType: "document" | "image";
  summary: string;
  url?: string;
  hasEmbedding: boolean;
}

export type AssetKind = "image" | "video";

export interface AssetItem {
  id: string;
  name: string;
  kind: AssetKind;
  meta: string;
  tone: "a" | "b" | "c" | "d" | "e" | "f";
  url?: string;
}

export interface UsageSummary {
  imagesThisMonth: number;
  videosThisMonth: number;
}
