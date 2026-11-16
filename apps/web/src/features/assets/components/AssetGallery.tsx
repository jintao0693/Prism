"use client";

import { useMemo, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import MediaPreview from "@/components/media/MediaPreview";
import { listAssets, uploadAsset } from "@/features/assets";
import { createConversation } from "@/features/chat";
import { stashPendingReferences } from "@/lib/pending-refs";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import type { AssetItem, AssetKind } from "@/types/domain";
import styles from "./AssetGallery.module.css";

type Filter = "all" | AssetKind;

export interface AssetGalleryProps {
  workspaceId: string;
  initialAssets: AssetItem[];
}

export default function AssetGallery({
  workspaceId,
  initialAssets,
}: AssetGalleryProps) {
  const router = useRouter();
  const [filter, setFilter] = useState<Filter>("all");
  const [assets, setAssets] = useState(initialAssets);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [sendingId, setSendingId] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const fileRef = useRef<HTMLInputElement>(null);

  const filters: { id: Filter; label: string }[] = useMemo(
    () => [
      { id: "all", label: "全部" },
      { id: "image", label: "图片" },
      { id: "video", label: "视频" },
    ],
    [],
  );

  function refresh(nextFilter: Filter = filter) {
    startTransition(() => {
      void listAssets(workspaceId, nextFilter)
        .then(setAssets)
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "加载资产失败");
        });
    });
  }

  function changeFilter(next: Filter) {
    setFilter(next);
    setError(null);
    refresh(next);
  }

  async function onUpload(files: FileList | null) {
    if (!files?.length) return;
    setError(null);
    setUploading(true);
    try {
      for (const file of Array.from(files).slice(0, 8)) {
        if (!file.type.startsWith("image/")) {
          throw new Error("资产中心目前支持上传图片（PNG / JPG / WEBP / GIF）");
        }
        await uploadAsset(workspaceId, file);
      }
      refresh(filter === "video" ? "all" : filter);
      if (filter === "video") setFilter("all");
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setUploading(false);
    }
  }

  async function sendToChat(asset: AssetItem) {
    const ok =
      asset.kind === "image" || asset.previewKind === "poster";
    if (!ok || asset.previewKind === "video") {
      setError("仅图片可送回对话作参考（视频请先导出静帧或用海报图）");
      return;
    }
    setError(null);
    setStatus(null);
    setSendingId(asset.id);
    try {
      stashPendingReferences(workspaceId, [
        {
          id: asset.id,
          name: asset.name,
          thumbUrl: asset.thumbUrl || asset.url,
          url: asset.url,
        },
      ]);
      const created = await createConversation(
        workspaceId,
        `参考 · ${asset.name.slice(0, 24)}`,
      );
      router.push(
        routes.chatConversation(workspaceId, created.id, {
          referenceAssetIds: [asset.id],
        }),
      );
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "送回对话失败");
    } finally {
      setSendingId(null);
    }
  }

  return (
    <div className="page-enter">
      <PageHeader
        title="资产中心"
        description="生成结果与上传参考图统一归档；可一键送回对话做图生图 / 图生视频"
        actions={
          <>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              multiple
              hidden
              onChange={(e) => {
                void onUpload(e.target.files);
                e.target.value = "";
              }}
            />
            <Button
              variant="ghost"
              disabled={uploading}
              onClick={() => fileRef.current?.click()}
            >
              {uploading ? "上传中…" : "上传图片"}
            </Button>
          </>
        }
      />

      <div className={styles.filters}>
        {filters.map((f) => (
          <button
            key={f.id}
            type="button"
            className={cn(styles.filter, filter === f.id && styles.active)}
            onClick={() => changeFilter(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error ? (
        <p className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
      {status ? <p className={styles.status}>{status}</p> : null}

      <div className={cn(styles.grid, pending && styles.pending)}>
        {assets.length === 0 ? (
          <div className={styles.emptyBox}>
            <strong>还没有资产</strong>
            <p>
              在创作对话里生成图片/视频，或点右上角「上传图片」放入参考图，之后可在对话中附参考图改稿。
            </p>
          </div>
        ) : null}
        {assets.map((asset) => {
          const canSend =
            asset.kind === "image" || asset.previewKind === "poster";
          return (
            <article key={asset.id} className={styles.asset}>
              <div className={styles.mediaWrap}>
                {asset.url || asset.thumbUrl ? (
                  <MediaPreview
                    url={asset.url}
                    thumbUrl={asset.thumbUrl}
                    kind={asset.kind}
                    previewKind={asset.previewKind}
                    mimeType={asset.mimeType}
                    alt={asset.name}
                    className={styles.mediaImg}
                    preferThumb
                    controls={asset.previewKind === "video"}
                  />
                ) : (
                  <div className={cn(styles.media, `thumb-${asset.tone}`)} />
                )}
                {asset.kind === "video" ? (
                  <span className={styles.badge}>
                    {asset.previewKind === "poster" ? "视频海报" : "视频"}
                  </span>
                ) : null}
              </div>
              <div className={styles.cap}>
                <strong>{asset.name}</strong>
                <span>{asset.meta}</span>
                {canSend ? (
                  <button
                    type="button"
                    className={styles.sendBtn}
                    disabled={sendingId === asset.id}
                    onClick={() => void sendToChat(asset)}
                  >
                    {sendingId === asset.id ? "跳转中…" : "送回对话"}
                  </button>
                ) : (
                  <span className={styles.sendHint}>视频请用静帧作参考</span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
