export interface VolcengineProviderConfig {
  provider: string;
  enabled: boolean;
  baseUrl: string;
  chatModel: string;
  imageModel: string;
  videoModel: string;
  embeddingModel: string;
  apiKeyMasked: string;
  hasApiKey: boolean;
  note: string;
}

export interface VolcengineProviderUpdate {
  enabled?: boolean;
  baseUrl?: string;
  chatModel?: string;
  imageModel?: string;
  videoModel?: string;
  embeddingModel?: string;
  apiKey?: string;
  note?: string;
}

export interface ProviderTestResult {
  ok: boolean;
  message: string;
  detail?: string | null;
}
