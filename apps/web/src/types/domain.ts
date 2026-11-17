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
  status: "active" | "evergreen" | "archived";
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
  thumbUrl?: string;
}

export interface WorkspaceMember {
  userId: string;
  name: string;
  email: string;
  role: Role;
  avatarText: string;
}

export interface BrandPack {
  name: string;
  primaryColor: string;
  accentColor: string;
  primaryColorName: string;
  accentColorName: string;
  keywords: string[];
  forbidden: string[];
  toneHint: string;
}

export interface MediaOptions {
  size?: string;
  ratio?: string;
  seed?: number;
  variants?: number;
}

export interface ShareLinkResult {
  id: string;
  token: string;
  title: string;
  resourceType: string;
  resourceId: string;
  sharePath: string;
}

export type MessageRole = "user" | "assistant";

export interface GenerationResult {
  id: string;
  label: string;
  tone: "a" | "b" | "c" | "d" | "e" | "f";
  kind?: "image" | "video";
  url?: string;
  thumbUrl?: string;
  mimeType?: string;
  previewKind?: "image" | "video" | "poster";
  parentAssetId?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  toolLabel?: string;
  results?: GenerationResult[];
  createdAt: string;
  /** 前端流式气泡占位 */
  streaming?: boolean;
  /** 本地乐观消息发送失败，保留内容可重试 */
  failed?: boolean;
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
  thumbUrl?: string;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  itemType: "document" | "image";
  summary: string;
  url?: string;
  thumbUrl?: string;
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
  thumbUrl?: string;
  mimeType?: string;
  previewKind?: "image" | "video" | "poster";
  parentAssetId?: string;
}

export interface UsageSummary {
  imagesThisMonth: number;
  videosThisMonth: number;
  imagesSoftLimit?: number;
  videosSoftLimit?: number;
}
