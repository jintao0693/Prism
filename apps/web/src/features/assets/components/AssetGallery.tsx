"use client";

import { useMemo, useState, useTransition } from "react";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import { listAssets } from "@/features/assets";
import { cn } from "@/lib/cn";
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
  const [filter, setFilter] = useState<Filter>("all");
  const [assets, setAssets] = useState(initialAssets);
  const [pending, startTransition] = useTransition();

  const filters: { id: Filter; label: string }[] = useMemo(
    () => [
      { id: "all", label: "全部" },
      { id: "image", label: "图片" },
      { id: "video", label: "视频" },
    ],
    [],
  );

  function changeFilter(next: Filter) {
    setFilter(next);
    startTransition(() => {
      void listAssets(workspaceId, next).then(setAssets);
    });
  }

  return (
    <div className="page-enter">
      <PageHeader
        title="资产中心"
        description="当前工作空间内的生成与上传素材"
        actions={
          <Button variant="ghost" disabled title="本地上传入口即将开放">
            上传 · 即将支持
          </Button>
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

      <div className={cn(styles.grid, pending && styles.pending)}>
        {assets.map((asset) => (
          <article key={asset.id} className={styles.asset}>
            <div className={cn(styles.media, `thumb-${asset.tone}`)} />
            <div className={styles.cap}>
              <strong>{asset.name}</strong>
              <span>{asset.meta}</span>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
