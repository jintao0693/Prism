# Prism Web

Next.js（App Router）+ TypeScript 前端。设计对齐 `design/prism-ui`。

## 开发

```bash
cd apps/web
npm install
npm run dev
```

打开 [http://localhost:3000](http://localhost:3000)，默认进入工作空间选择页。

## 目录约定

| 路径 | 职责 |
|------|------|
| `src/app` | 路由页面（尽量薄，只组装） |
| `src/components/ui` | 通用原子组件 |
| `src/components/layout` | 壳：Topbar / Sidebar / AppShell |
| `src/features/*` | 按业务域：`api` + `components` |
| `src/lib` | 路由常量、API 客户端、工具 |
| `src/types` | 领域类型 |

当前 `features/*/api` 使用 **mock 数据**。后端就绪后把 `NEXT_PUBLIC_USE_MOCK=false` 并实现 `lib/api-client.ts` 真实请求。

## 主要路由

- `/workspaces` 工作空间
- `/w/[workspaceId]` 工作台
- `/w/[workspaceId]/chat/[conversationId]` 创作对话
- `/w/[workspaceId]/knowledge` 知识库
- `/w/[workspaceId]/assets` 资产中心
- `/w/[workspaceId]/settings` 设置
