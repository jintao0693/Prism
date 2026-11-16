import { apiRequest, USE_MOCK } from "@/lib/api-client";
import { mockDelay } from "@/lib/mock-delay";

export type GenerationJobItem = {
  id: string;
  jobType: string;
  status: string;
  prompt: string;
  resultAssetId?: string | null;
  errorMessage?: string | null;
  conversationId?: string | null;
  progressStatus?: string | null;
  progressElapsed?: number;
  createdAt?: string;
};

function mapJob(raw: Record<string, unknown>): GenerationJobItem {
  return {
    id: String(raw.id),
    jobType: String(raw.jobType ?? raw.job_type ?? "video"),
    status: String(raw.status ?? "queued"),
    prompt: String(raw.prompt ?? ""),
    resultAssetId:
      raw.resultAssetId != null
        ? String(raw.resultAssetId)
        : raw.result_asset_id != null
          ? String(raw.result_asset_id)
          : null,
    errorMessage:
      raw.errorMessage != null
        ? String(raw.errorMessage)
        : raw.error_message != null
          ? String(raw.error_message)
          : null,
    conversationId:
      raw.conversationId != null
        ? String(raw.conversationId)
        : raw.conversation_id != null
          ? String(raw.conversation_id)
          : null,
    progressStatus:
      raw.progressStatus != null
        ? String(raw.progressStatus)
        : raw.progress_status != null
          ? String(raw.progress_status)
          : null,
    progressElapsed: Number(
      raw.progressElapsed ?? raw.progress_elapsed ?? 0,
    ),
    createdAt:
      raw.createdAt != null
        ? String(raw.createdAt)
        : raw.created_at != null
          ? String(raw.created_at)
          : undefined,
  };
}

export async function listJobs(
  workspaceId: string,
): Promise<GenerationJobItem[]> {
  if (USE_MOCK) {
    await mockDelay();
    return [];
  }
  const raw = await apiRequest<Record<string, unknown>[]>(
    "/jobs",
    {},
    { workspaceId },
  );
  return raw.map(mapJob);
}

export async function getJob(
  workspaceId: string,
  jobId: string,
): Promise<GenerationJobItem> {
  if (USE_MOCK) {
    await mockDelay();
    return {
      id: jobId,
      jobType: "video",
      status: "succeeded",
      prompt: "mock",
    };
  }
  const raw = await apiRequest<Record<string, unknown>>(
    `/jobs/${jobId}`,
    {},
    { workspaceId },
  );
  return mapJob(raw);
}
