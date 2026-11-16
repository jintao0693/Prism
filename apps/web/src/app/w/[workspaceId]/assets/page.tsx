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
    <AssetGallery workspaceId={workspaceId} initialAssets={assets} />
  );
}
