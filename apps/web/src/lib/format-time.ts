/** 相对时间与会话时间展示。 */

export function formatRelativeTime(isoOrLabel: string | undefined | null): string {
  if (!isoOrLabel) return "";
  const parsed = Date.parse(isoOrLabel);
  if (Number.isNaN(parsed)) return isoOrLabel;
  const diffSec = Math.round((Date.now() - parsed) / 1000);
  if (diffSec < 45) return "刚刚";
  if (diffSec < 3600) return `${Math.max(1, Math.floor(diffSec / 60))} 分钟前`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} 小时前`;
  if (diffSec < 86400 * 7) return `${Math.floor(diffSec / 86400)} 天前`;
  const d = new Date(parsed);
  const now = new Date();
  const sameYear = d.getFullYear() === now.getFullYear();
  return sameYear
    ? `${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    : `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
}

export function formatClock(iso: string | undefined | null): string {
  if (!iso) return "";
  const parsed = Date.parse(iso);
  if (Number.isNaN(parsed)) return "";
  const d = new Date(parsed);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function pad(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}
