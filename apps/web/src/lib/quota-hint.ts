import type { UsageSummary } from "@/types/domain";

const DEFAULT_IMAGE_SOFT = 50;
const DEFAULT_VIDEO_SOFT = 10;
/** 达到软上限的该比例时开始轻提示 */
const WARN_RATIO = 0.8;

export function formatQuotaHint(usage: UsageSummary | null | undefined): string | null {
  if (!usage) return null;
  const imgLimit = usage.imagesSoftLimit ?? DEFAULT_IMAGE_SOFT;
  const vidLimit = usage.videosSoftLimit ?? DEFAULT_VIDEO_SOFT;
  const imgWarn = Math.floor(imgLimit * WARN_RATIO);
  const vidWarn = Math.floor(vidLimit * WARN_RATIO);

  const parts: string[] = [];
  if (usage.imagesThisMonth >= imgLimit) {
    parts.push(`本月生图已达软上限 ${imgLimit} 张`);
  } else if (usage.imagesThisMonth >= imgWarn) {
    parts.push(`本月生图 ${usage.imagesThisMonth}/${imgLimit}，接近上限`);
  }
  if (usage.videosThisMonth >= vidLimit) {
    parts.push(`本月视频已达软上限 ${vidLimit} 条`);
  } else if (usage.videosThisMonth >= vidWarn) {
    parts.push(`本月视频 ${usage.videosThisMonth}/${vidLimit}，接近上限`);
  }
  return parts.length ? parts.join(" · ") : null;
}
