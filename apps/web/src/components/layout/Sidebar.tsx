"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import type { UsageSummary } from "@/types/domain";
import SpectrumBar from "@/components/ui/SpectrumBar";
import styles from "./Sidebar.module.css";

export interface SidebarProps {
  workspaceId: string;
  usage: UsageSummary;
}

interface NavItem {
  href: string;
  label: string;
  icon: string;
  match: (pathname: string) => boolean;
}

export default function Sidebar({ workspaceId, usage }: SidebarProps) {
  const pathname = usePathname();

  const items: NavItem[] = [
    {
      href: routes.workspaceHome(workspaceId),
      label: "工作台",
      icon: "◈",
      match: (p) => p === routes.workspaceHome(workspaceId),
    },
    {
      href: routes.chat(workspaceId),
      label: "创作对话",
      icon: "✎",
      match: (p) => p.startsWith(routes.chat(workspaceId)),
    },
    {
      href: routes.knowledge(workspaceId),
      label: "知识库",
      icon: "▣",
      match: (p) => p.startsWith(routes.knowledge(workspaceId)),
    },
    {
      href: routes.assets(workspaceId),
      label: "资产中心",
      icon: "▦",
      match: (p) => p.startsWith(routes.assets(workspaceId)),
    },
  ];

  return (
    <aside className={styles.nav}>
      <div className={styles.label}>空间</div>
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(styles.item, item.match(pathname) && styles.active)}
        >
          <span className={styles.ico} aria-hidden>
            {item.icon}
          </span>
          <span className={styles.text}>{item.label}</span>
        </Link>
      ))}

      <div className={styles.label} style={{ marginTop: 18 }}>
        后续
      </div>
      <span className={cn(styles.item, styles.soon)}>
        <span className={styles.ico} aria-hidden>
          ↗
        </span>
        <span className={styles.text}>发布</span>
        <span className={styles.badge}>Phase 2</span>
      </span>
      <span className={cn(styles.item, styles.soon)}>
        <span className={styles.ico} aria-hidden>
          ◎
        </span>
        <span className={styles.text}>投放</span>
        <span className={styles.badge}>Phase 3</span>
      </span>

      <Link
        href={routes.settings(workspaceId)}
        className={cn(
          styles.item,
          pathname.startsWith(routes.settings(workspaceId)) && styles.active,
        )}
      >
        <span className={styles.ico} aria-hidden>
          ⚙
        </span>
        <span className={styles.text}>设置</span>
      </Link>

      <div className={styles.foot}>
        <SpectrumBar />
        <p>
          本月已生成 {usage.imagesThisMonth} 张图 · {usage.videosThisMonth}{" "}
          条视频
        </p>
      </div>
    </aside>
  );
}
