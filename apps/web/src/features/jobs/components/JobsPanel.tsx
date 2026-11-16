"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Button from "@/components/ui/Button";
import PageHeader from "@/components/ui/PageHeader";
import Panel from "@/components/ui/Panel";
import { listJobs, type GenerationJobItem } from "@/features/jobs/api/jobsApi";
import { cn } from "@/lib/cn";
import { formatRelativeTime } from "@/lib/format-time";
import { routes } from "@/lib/routes";
import styles from "./JobsPanel.module.css";

export default function JobsPanel({ workspaceId }: { workspaceId: string }) {
  const [jobs, setJobs] = useState<GenerationJobItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  async function refresh(manual = false) {
    if (manual) setRefreshing(true);
    try {
      const data = await listJobs(workspaceId);
      setJobs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载任务失败");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => {
      void refresh();
    }, 4000);
    return () => window.clearInterval(timer);
  }, [workspaceId]);

  const hasActive = jobs.some(
    (j) => j.status === "running" || j.status === "queued",
  );

  return (
    <div className={`page-enter ${styles.wrap}`}>
      <PageHeader
        title="任务中心"
        description="视频等长任务可在此回看；关闭对话页也不会丢进度。"
        actions={
          <Button
            variant="ghost"
            disabled={refreshing}
            onClick={() => void refresh(true)}
          >
            {refreshing ? "刷新中…" : "刷新"}
          </Button>
        }
      />
      <Panel className={styles.panel}>
        {loading ? <p className={styles.muted}>加载中…</p> : null}
        {error ? (
          <p className={styles.err} role="alert">
            {error}
          </p>
        ) : null}
        {!loading && !jobs.length ? (
          <div className={styles.empty}>
            <strong>还没有生成任务</strong>
            <p>
              在创作对话里说「做成预告」即可。进行中的任务也会出现在这里。
            </p>
            <Link href={routes.chat(workspaceId)}>去创作对话</Link>
          </div>
        ) : null}
        {hasActive ? (
          <p className={styles.liveHint} role="status">
            有任务进行中，列表约每 4 秒自动更新。
          </p>
        ) : null}
        <ul className={styles.list}>
          {jobs.map((job) => (
            <li
              key={job.id}
              className={cn(styles.item, styles[`st_${job.status}`])}
            >
              <div className={styles.top}>
                <div className={styles.titleRow}>
                  <span className={cn(styles.chip, styles[`chip_${job.status}`])}>
                    {statusLabel(job.status)}
                  </span>
                  <strong>
                    {job.jobType === "video" ? "视频生成" : job.jobType}
                  </strong>
                </div>
                <span className={styles.time}>
                  {formatRelativeTime(job.createdAt)}
                </span>
              </div>
              <p className={styles.prompt}>{job.prompt || "（无提示词）"}</p>
              {job.status === "running" || job.status === "queued" ? (
                <div className={styles.progressBlock}>
                  <div className={styles.barTrack} aria-hidden>
                    <div className={styles.barFill} />
                  </div>
                  <p className={styles.progress}>
                    {job.progressStatus || "处理中"}
                    {job.progressElapsed
                      ? ` · ${Math.round(job.progressElapsed)}s`
                      : ""}
                  </p>
                </div>
              ) : null}
              {job.errorMessage ? (
                <p className={styles.err}>{job.errorMessage}</p>
              ) : null}
              <div className={styles.links}>
                {job.conversationId ? (
                  <Link
                    href={routes.chatConversation(
                      workspaceId,
                      job.conversationId,
                    )}
                  >
                    打开会话
                  </Link>
                ) : null}
                {job.resultAssetId ? (
                  <Link
                    href={`${routes.assets(workspaceId)}?highlight=${encodeURIComponent(job.resultAssetId)}`}
                  >
                    查看成片
                  </Link>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}

function statusLabel(status: string): string {
  if (status === "succeeded") return "已完成";
  if (status === "failed") return "失败";
  if (status === "running") return "进行中";
  if (status === "queued") return "排队中";
  return status;
}
