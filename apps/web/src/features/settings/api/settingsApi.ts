import { apiRequest, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";
import type {
  ProviderTestResult,
  VolcengineProviderConfig,
  VolcengineProviderUpdate,
} from "@/features/settings/types";

const MOCK_CONFIG: VolcengineProviderConfig = {
  provider: "volcengine_ark",
  enabled: false,
  baseUrl: "https://ark.cn-beijing.volces.com/api/v3",
  chatModel: "doubao-seed-1-6-251015",
  imageModel: "doubao-seedream-4-0-250828",
  videoModel: "doubao-seedance-1-0-pro-250528",
  embeddingModel: "doubao-embedding-vision-250615",
  apiKeyMasked: "",
  hasApiKey: false,
  note: "请连接后端后配置真实 Key",
};

function mapConfig(raw: Record<string, unknown>): VolcengineProviderConfig {
  return {
    provider: String(raw.provider ?? "volcengine_ark"),
    enabled: Boolean(raw.enabled),
    baseUrl: String(raw.base_url ?? raw.baseUrl ?? ""),
    chatModel: String(raw.chat_model ?? raw.chatModel ?? ""),
    imageModel: String(raw.image_model ?? raw.imageModel ?? ""),
    videoModel: String(raw.video_model ?? raw.videoModel ?? ""),
    embeddingModel: String(raw.embedding_model ?? raw.embeddingModel ?? ""),
    apiKeyMasked: String(raw.api_key_masked ?? raw.apiKeyMasked ?? ""),
    hasApiKey: Boolean(raw.has_api_key ?? raw.hasApiKey),
    note: String(raw.note ?? ""),
  };
}

export async function getVolcengineConfig(): Promise<VolcengineProviderConfig> {
  if (USE_MOCK) {
    await mockDelay();
    return MOCK_CONFIG;
  }
  const raw = await apiRequest<Record<string, unknown>>(
    "/settings/providers/volcengine",
  );
  return mapConfig(raw);
}

export async function updateVolcengineConfig(
  body: VolcengineProviderUpdate,
): Promise<VolcengineProviderConfig> {
  if (USE_MOCK) {
    await mockDelay();
    return {
      ...MOCK_CONFIG,
      ...body,
      apiKeyMasked: body.apiKey ? `****${body.apiKey.slice(-4)}` : MOCK_CONFIG.apiKeyMasked,
      hasApiKey: Boolean(body.apiKey) || MOCK_CONFIG.hasApiKey,
      enabled: body.enabled ?? MOCK_CONFIG.enabled,
    };
  }
  const raw = await apiRequest<Record<string, unknown>>(
    "/settings/providers/volcengine",
    {
      method: "PUT",
      body: JSON.stringify({
        enabled: body.enabled,
        baseUrl: body.baseUrl,
        chatModel: body.chatModel,
        imageModel: body.imageModel,
        videoModel: body.videoModel,
        embeddingModel: body.embeddingModel,
        apiKey: body.apiKey,
        note: body.note,
      }),
    },
  );
  return mapConfig(raw);
}

export async function testVolcengineConnection(): Promise<ProviderTestResult> {
  if (USE_MOCK) {
    await mockDelay(400);
    return {
      ok: false,
      message: "当前为前端 Mock",
      detail: "请设置 NEXT_PUBLIC_USE_MOCK=false 并启动后端",
    };
  }
  return apiRequest<ProviderTestResult>("/settings/providers/volcengine/test", {
    method: "POST",
    body: "{}",
  });
}
