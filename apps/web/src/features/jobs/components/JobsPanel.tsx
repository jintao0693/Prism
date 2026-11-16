"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PageHeader from "@/components/ui/PageHeader";
import Panel from "@/components/ui/Panel";
import { listJobs, type GenerationJobItem } from "@/features/jobs/api/jobsApi";
import { routes } from "@/lib/routes";
import styles from "./JobsPanel.module.css";

export default function JobsPanel({ workspaceId }: { workspaceId: string }) {
  const [jobs, setJobs] = useState<GenerationJobItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      const data = await listJobs(workspaceId);
      setJobs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载任务失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => {
      void refresh();
    }, 4000);
    return () => window.clearInterval(timer);
  }, [workspaceId]);

  return (
    <div className={`page-enter ${styles.wrap}`}>
      <PageHeader
        title="任务中心"
        description="视频等长任务可在此回看进度；关闭对话页也不会丢。"
      />
      <Panel className={styles.panel}>
        {loading ? <p className={styles.muted}>加载中…</p> : null}
        {error ? <p className={styles.err}>{error}</p> : null}
        {!loading && !jobs.length ? (
          <p className={styles.muted}>还没有生成任务。去创作对话里发起图生视频即可。</p>
        ) : null}
        <ul className={styles.list}>
          {jobs.map((job) => (
            <li key={job.id} className={styles.item}>
              <div className={styles.top}>
                <strong>
                  {job.jobType === "video" ? "视频" : job.jobType} ·{" "}
                  {statusLabel(job.status)}
                </strong>
                <span className={styles.time}>
                  {job.createdAt
                    ? new Date(job.createdAt).toLocaleString()
                    : ""}
                </span>
              </div>
              <p className={styles.prompt}>{job.prompt || "（无提示词）"}</p>
              {job.status === "running" || job.status === "queued" ? (
                <p className={styles.progress}>
                  {job.progressStatus || "处理中"}
                  {job.progressElapsed
                    ? ` · ${Math.round(job.progressElapsed)}s`
                    : ""}
                </p>
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
                  <Link href={routes.assets(workspaceId)}>查看资产中心</Link>
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
