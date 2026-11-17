import Link from "next/link";
import PageHeader from "@/components/ui/PageHeader";
import Panel from "@/components/ui/Panel";
import { routes } from "@/lib/routes";
import styles from "./page.module.css";

const CASES = [
  {
    title: "案例 1 · 发行 brief",
    desc: "知识库问答对齐主色、点缀色与立绘禁忌。",
  },
  {
    title: "案例 2 · 商店 KV",
    desc: "一句话出主视觉，再「偏暖」图生图改稿，保留构图。",
  },
  {
    title: "案例 3 · 氛围预告",
    desc: "静帧 → 5 秒图生视频，进度 SSE + 任务中心可查。",
  },
  {
    title: "高级 A · 母版血缘",
    desc: "资产中心 A/B 对比母版与改稿，分享只读链接对外评审。",
  },
] as const;

export default function CasesPage() {
  return (
    <main className={styles.wrap}>
      <PageHeader
        title="游戏发行案例"
        description="《幻境：星落传说》演示路径：规范 → KV → 预告 → 血缘改稿"
      />
      <Panel className={styles.panel}>
        <p className={styles.lead}>
          完整脚本与素材说明见仓库{" "}
          <a
            href="https://github.com/jintao0693/Prism/blob/main/docs/GAME_CASES.md"
            target="_blank"
            rel="noreferrer"
          >
            docs/GAME_CASES.md
          </a>
          。本地可运行 <code>python scripts/run_game_cases.py</code>。
        </p>
        <ul className={styles.list}>
          {CASES.map((item) => (
            <li key={item.title}>
              <strong>{item.title}</strong>
              <span>{item.desc}</span>
            </li>
          ))}
        </ul>
        <div className={styles.actions}>
          <Link className={styles.primary} href={routes.workspaces}>
            进入工作空间
          </Link>
          <Link className={styles.ghost} href={routes.login}>
            登录演示账号
          </Link>
        </div>
      </Panel>
    </main>
  );
}