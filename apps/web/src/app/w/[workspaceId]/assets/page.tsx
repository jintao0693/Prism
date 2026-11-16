import { Suspense } from "react";
import AssetGallery from "@/features/assets/components/AssetGallery";
import { listAssets } from "@/features/assets";

export default async function AssetsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const assets = await listAssets(workspaceId);

  return (
    <Suspense fallback={<p style={{ padding: 24 }}>加载资产…</p>}>
      <AssetGallery workspaceId={workspaceId} initialAssets={assets} />
    </Suspense>
  );
}
