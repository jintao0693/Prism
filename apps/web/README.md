# Prism Web

Next.js 15（App Router）+ TypeScript 前端控制台。视觉与交互对齐 `design/prism-ui`。

| | |
|---|---|
| **开发者** | [jintao](https://github.com/jintao0693) |
| **默认端口** | `3000` |
| **对接 API** | `NEXT_PUBLIC_API_BASE_URL`（默认 `http://127.0.0.1:8000`） |

---

## 功能页面

| 路由 | 说明 |
|------|------|
| `/login` | 登录（真实 API 时写 cookie，便于 RSC） |
| `/workspaces` | 工作空间选择 |
| `/w/[workspaceId]` | 工作台首页 |
| `/w/[workspaceId]/chat` | 创作对话列表 / 新建 |
| `/w/[workspaceId]/chat/[conversationId]` | 会话详情与流式回复 |
| `/w/[workspaceId]/knowledge` | 知识库列表 |
| `/w/[workspaceId]/knowledge/[kbId]` | 知识库详情 / 检索 |
| `/w/[workspaceId]/assets` | 资产中心 |
| `/w/[workspaceId]/settings` | 租户设置（含火山方舟） |

---

## 本地开发

```bash
cd apps/web
npm install
```

配置 `.env.local`（可从 `.env.example` 复制）：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_USE_MOCK=false
```

| 变量 | 说明 |
|------|------|
| `NEXT_PUBLIC_API_BASE_URL` | 后端根地址（不含 `/api/v1` 时以客户端实现为准） |
| `NEXT_PUBLIC_USE_MOCK` | `true` 用前端 mock；接真后端请设 `false` |

```bash
npm run dev
```

打开 http://localhost:3000 。演示账号见根 README / API README。

生产构建：

```bash
npm run build
npm start
```

---

## 目录约定

| 路径 | 职责 |
|------|------|
| `src/app` | 路由页面（薄：只组装 features） |
| `src/components/ui` | 原子组件（Button、Panel、BrandMark…） |
| `src/components/layout` | Topbar / Sidebar / AppShell / WorkspacePill |
| `src/features/*` | 业务域：`api` + `components` |
| `src/lib` | `api-client`、路由常量、工具 |
| `src/types` | 领域类型 |
| `src/styles` | 全局样式与设计 token |

### Features 一览

| Feature | 作用 |
|---------|------|
| `auth` | 登录 / me |
| `workspace` | 工作空间列表与卡片 |
| `chat` | 会话列表、Composer、消息气泡 |
| `knowledge` | 知识库列表与详情检索 |
| `assets` | 资产画廊 |
| `settings` | 用量与火山 Provider 表单 |
| `home` | 工作台仪表盘 |

---

## 与后端联调

1. 先启动 `apps/api`（端口 8000）  
2. `NEXT_PUBLIC_USE_MOCK=false`  
3. 登录后进入 **设置**，填写火山 API Key 与模型 ID，启用并测试连通  
4. 再在对话中验证问答 / 生图 / 生视频  

请求头由客户端自动附带 JWT；工作空间 ID 经 `WorkspaceContextBridge` 注入。

---

## 开发者

维护者：**jintao**（[@jintao0693](https://github.com/jintao0693)）  
许可：与仓库根目录 MIT 一致。
