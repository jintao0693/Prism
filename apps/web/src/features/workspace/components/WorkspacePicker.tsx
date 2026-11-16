import BrandMark from "@/components/ui/BrandMark";
import SpectrumBar from "@/components/ui/SpectrumBar";
import Avatar from "@/components/ui/Avatar";
import WorkspaceCard from "@/features/workspace/components/WorkspaceCard";
import type { Tenant, User, Workspace } from "@/types/domain";
import styles from "./WorkspacePicker.module.css";

export interface WorkspacePickerProps {
  tenant: Tenant;
  user: User;
  workspaces: Workspace[];
}

export default function WorkspacePicker({
  tenant,
  user,
  workspaces,
}: WorkspacePickerProps) {
  return (
    <section className={styles.screen}>
      <header className={styles.top}>
        <BrandMark />
        <div className={styles.topRight}>
          <span className={styles.tenant}>
            {tenant.name}
          </span>
          <Avatar text={user.avatarText} />
        </div>
      </header>

      <div className={styles.hero}>
        <div className={styles.eyebrow}>
          <SpectrumBar width={36} />
          选择工作空间
        </div>
        <h1>
          把灵感折进 <span>Prism</span>
        </h1>
        <p>
          对话驱动生图与生视频，知识库支持以图搜图。每个工作空间独立沉淀素材与品牌语境。
        </p>
      </div>

      <div className={styles.grid}>
        {workspaces.map((ws) => (
          <WorkspaceCard key={ws.id} workspace={ws} />
        ))}
        <button type="button" className={styles.create} disabled>
          <span className={styles.plus}>＋</span>
          <span>新建工作空间</span>
        </button>
      </div>
    </section>
  );
}
