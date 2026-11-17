"use client";

import { useEffect, useMemo, useRef, useState, useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import MediaPreview from "@/components/media/MediaPreview";
import MediaLightbox from "@/components/media/MediaLightbox";
import { listAssets, uploadAsset } from "@/features/assets";
import { createConversation, listConversations } from "@/features/chat";
import { createAssetShare } from "@/features/shares/api/sharesApi";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
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
  const searchParams = useSearchParams();
  const [filter, setFilter] = useState<Filter>("all");
  const [assets, setAssets] = useState(initialAssets);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<AssetItem | null>(null);
  const [sendTarget, setSendTarget] = useState<AssetItem | null>(null);
  const [comparePair, setComparePair] = useState<{
    parent: AssetItem;
    current: AssetItem;
  } | null>(null);
  const [sharingId, setSharingId] = useState<string | null>(null);
  const highlightId = searchParams.get("highlight");

  useEffect(() => {
    if (!highlightId) return;
    const el = document.getElementById(`asset-${highlightId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightId, assets]);
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

  function requestSendToChat(asset: AssetItem) {
    const ok =
      asset.kind === "image" || asset.previewKind === "poster";
    if (!ok || asset.previewKind === "video") {
      setError("仅图片可送回对话作参考（视频请先导出静帧或用海报图）");
      return;
    }
    setSendTarget(asset);
  }

  async function shareAsset(asset: AssetItem) {
    setError(null);
    setStatus(null);
    setSharingId(asset.id);
    try {
      const link = await createAssetShare(workspaceId, asset.id, {
        title: asset.name,
      });
      const path = link.sharePath || routes.share(link.token);
      const url =
        typeof window !== "undefined"
          ? `${window.location.origin}${path}`
          : path;
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(url);
        setStatus("分享链接已复制到剪贴板");
      } else {
        setStatus(`分享链接：${url}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建分享失败");
    } finally {
      setSharingId(null);
    }
  }

  function openCompare(asset: AssetItem) {
    if (!asset.parentAssetId) return;
    const parent = assets.find((a) => a.id === asset.parentAssetId);
    if (!parent) {
      setError("找不到母版图，无法对比");
      return;
    }
    setComparePair({ parent, current: asset });
  }

  async function sendToChat(asset: AssetItem, mode: "recent" | "new") {
    setError(null);
    setStatus(null);
    setSendingId(asset.id);
    setSendTarget(null);
    try {
      stashPendingReferences(workspaceId, [
        {
          id: asset.id,
          name: asset.name,
          thumbUrl: asset.thumbUrl || asset.url,
          url: asset.url,
        },
      ]);
      let conversationId: string;
      if (mode === "recent") {
        const list = await listConversations(workspaceId);
        if (list[0]) {
          conversationId = list[0].id;
        } else {
          const created = await createConversation(
            workspaceId,
            `参考 · ${asset.name.slice(0, 24)}`,
          );
          conversationId = created.id;
        }
      } else {
        const created = await createConversation(
          workspaceId,
          `参考 · ${asset.name.slice(0, 24)}`,
        );
        conversationId = created.id;
      }
      router.push(
        routes.chatConversation(workspaceId, conversationId, {
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
          const parent = asset.parentAssetId
            ? assets.find((a) => a.id === asset.parentAssetId)
            : undefined;
          const lineage = asset.parentAssetId
            ? parent
              ? `基于「${parent.name}」改稿`
              : `基于 ${asset.parentAssetId.slice(0, 10)}… 改稿`
            : null;
          return (
            <article
              key={asset.id}
              className={cn(
                styles.asset,
                highlightId === asset.id && styles.highlight,
              )}
              id={`asset-${asset.id}`}
            >
              <button
                type="button"
                className={styles.mediaWrap}
                onClick={() => {
                  if (asset.url || asset.thumbUrl) setPreview(asset);
                }}
              >
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
                    controls={false}
                  />
                ) : (
                  <div className={cn(styles.media, `thumb-${asset.tone}`)} />
                )}
                {asset.kind === "video" ? (
                  <span className={styles.badge}>
                    {asset.previewKind === "poster" ? "视频海报" : "视频"}
                  </span>
                ) : null}
              </button>
              <div className={styles.cap}>
                <strong>{asset.name}</strong>
                <span>{asset.meta}</span>
                {lineage ? <em className={styles.lineage}>{lineage}</em> : null}
                <div className={styles.actionRow}>
                  <button
                    type="button"
                    className={styles.sendBtn}
                    disabled={sharingId === asset.id}
                    onClick={() => void shareAsset(asset)}
                  >
                    {sharingId === asset.id ? "生成中…" : "分享"}
                  </button>
                  {asset.parentAssetId ? (
                    <button
                      type="button"
                      className={styles.sendBtn}
                      onClick={() => openCompare(asset)}
                    >
                      A/B 对比
                    </button>
                  ) : null}
                  {canSend ? (
                    <button
                      type="button"
                      className={styles.sendBtn}
                      disabled={sendingId === asset.id}
                      onClick={() => requestSendToChat(asset)}
                    >
                      {sendingId === asset.id ? "跳转中…" : "送回对话"}
                    </button>
                  ) : (
                    <span className={styles.sendHint}>视频请用静帧作参考</span>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>

      <MediaLightbox
        open={Boolean(preview)}
        onClose={() => setPreview(null)}
        url={preview?.url}
        thumbUrl={preview?.thumbUrl}
        kind={preview?.kind}
        previewKind={preview?.previewKind}
        mimeType={preview?.mimeType}
        title={preview?.name}
        lineageLabel={
          preview?.parentAssetId
            ? `基于 ${preview.parentAssetId.slice(0, 10)}… 改稿`
            : null
        }
      />

      {comparePair ? (
        <div className={styles.compareOverlay} role="dialog" aria-modal>
          <div className={styles.compareCard}>
            <div className={styles.compareHead}>
              <strong>A/B 对比 · 母版 vs 当前</strong>
              <button
                type="button"
                onClick={() => setComparePair(null)}
              >
                关闭
              </button>
            </div>
            <div className={styles.compareGrid}>
              <div>
                <span className={styles.compareLabel}>母版</span>
                <MediaPreview
                  url={comparePair.parent.url}
                  thumbUrl={comparePair.parent.thumbUrl}
                  kind={comparePair.parent.kind}
                  previewKind={comparePair.parent.previewKind}
                  mimeType={comparePair.parent.mimeType}
                  alt={comparePair.parent.name}
                  className={styles.compareMedia}
                  preferThumb
                  controls={false}
                />
                <p>{comparePair.parent.name}</p>
              </div>
              <div>
                <span className={styles.compareLabel}>当前</span>
                <MediaPreview
                  url={comparePair.current.url}
                  thumbUrl={comparePair.current.thumbUrl}
                  kind={comparePair.current.kind}
                  previewKind={comparePair.current.previewKind}
                  mimeType={comparePair.current.mimeType}
                  alt={comparePair.current.name}
                  className={styles.compareMedia}
                  preferThumb
                  controls={false}
                />
                <p>{comparePair.current.name}</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <ConfirmDialog
        open={Boolean(sendTarget)}
        title="送回对话"
        description={
          <>
            将「{sendTarget?.name}」作为参考图。可加入最近会话，或新开一轮改稿。
          </>
        }
        confirmLabel="加入最近会话"
        secondaryLabel="新开对话"
        cancelLabel="取消"
        onConfirm={() => {
          if (sendTarget) void sendToChat(sendTarget, "recent");
        }}
        onSecondary={() => {
          if (sendTarget) void sendToChat(sendTarget, "new");
        }}
        onCancel={() => setSendTarget(null)}
      />
    </div>
  );
}
