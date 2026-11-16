# Prism 代码目录与结构

> 仓库形态：**Monorepo**  
> 作者 / 开发者：**jintao**（[@jintao0693](https://github.com/jintao0693)）  
> 默认栈（已选定）：**Next.js（App Router）+ TypeScript 前端 + FastAPI 后端 + Pydantic AI Harness + PostgreSQL/pgvector + Redis + S3 兼容存储**  
> 原则：按业务域分包，MVP 只建会用到的目录；Phase 2/3 目录可先占位空 `__init__` / README，不写死逻辑。

---

## 1. 顶层一览

```
Prism/
├── apps/
│   ├── web/                 # 前端（Next.js App Router + TS）
│   └── api/                 # 后端 API + Worker 入口（FastAPI / Python）
├── design/
│   └── prism-ui/            # 界面草稿（HTML）
├── docs/                    # PRODUCT / TECHNICAL / IA / STRUCTURE / PROGRESS
├── infra/                   # docker-compose（依赖 + profile full）
├── scripts/                 # dev.ps1 / dev.sh
├── .github/                 # CI、Issue / PR 模板
├── AUTHORS.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile                 # 偏 Unix；Windows 请用 scripts/dev.ps1
├── README.md
├── ROADMAP.md
└── SECURITY.md
```

> `packages/`、根级 `pnpm-workspace.yaml` 为可选后期规划，当前仓库尚未创建。

**边界**

| 路径 | 职责 | 不放什么 |
|------|------|----------|
| `apps/web` | UI、路由、调用 API | 业务算法、直连数据库 |
| `apps/api` | HTTP/SSE、领域服务、任务投递 | 页面组件 |
| `infra` | 本地依赖与部署 | 业务代码 |
| `docs` / `design` | 文档与设计稿 | 运行时依赖 |

---

## 2. 前端 `apps/web`

```
apps/web/
├── package.json
├── next.config.ts
├── tsconfig.json
├── public/
├── src/
│   ├── app/                          # App Router
│   │   ├── layout.tsx
│   │   ├── (auth)/
│   │   │   └── login/page.tsx
│   │   ├── (app)/                    # 需登录的壳
│   │   │   ├── layout.tsx            # 顶栏 + 侧栏
│   │   │   ├── workspaces/
│   │   │   │   └── page.tsx          # 工作空间选择
│   │   │   ├── w/[workspaceId]/      # 进入某空间后
│   │   │   │   ├── page.tsx          # 工作台
│   │   │   │   ├── chat/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── [conversationId]/page.tsx
│   │   │   │   ├── knowledge/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── [kbId]/page.tsx
│   │   │   │   ├── assets/page.tsx
│   │   │   │   └── settings/page.tsx
│   │   │   └── settings/             # 租户级设置（若与空间设置分离）
│   │   └── api/                      # 仅 BFF 代理时使用（可选）
│   ├── components/
│   │   ├── ui/                       # 按钮、输入、面板等原子组件
│   │   ├── layout/                   # Topbar、Sidebar、WorkspacePill
│   │   ├── chat/                     # 消息气泡、结果卡片、Composer
│   │   ├── knowledge/                # 库卡片、图搜区
│   │   └── assets/                   # 网格、筛选
│   ├── features/                     # 按功能聚合 hooks + api 调用
│   │   ├── auth/
│   │   ├── workspace/
│   │   ├── chat/
│   │   ├── knowledge/
│   │   ├── assets/
│   │   └── settings/
│   ├── lib/
│   │   ├── api-client.ts             # fetch 封装 + tenant/workspace header
│   │   ├── auth.ts
│   │   └── utils.ts
│   ├── styles/
│   │   └── globals.css               # 设计 token（对齐草稿光谱/青石色）
│   └── types/
│       └── api.ts
└── README.md
```

**约定**

- 路由带 `workspaceId`：`/w/[workspaceId]/...`，与后端 `X-Workspace-Id` 一致。
- `features/*` 只放该域的数据获取与状态；可复用 UI 放 `components`。
- Phase 2/3 页面可建路由但显示「即将推出」，或暂不建文件。

---

## 3. 后端 `apps/api`

```
apps/api/
├── pyproject.toml
├── README.md
├── alembic/                          # DB 迁移
│   └── versions/
├── app/
│   ├── main.py                       # FastAPI 装配
│   ├── worker.py                     # 异步 Worker 入口（同仓不同进程）
│   ├── core/
│   │   ├── config.py                 # 环境变量
│   │   ├── security.py               # JWT / 密钥加解密
│   │   ├── db.py                     # SQLAlchemy / 会话
│   │   ├── redis.py
│   │   ├── storage.py                # S3 客户端
│   │   └── logging.py
│   ├── middleware/
│   │   ├── tenant.py                 # 注入 TenantContext
│   │   └── workspace.py              # 校验 workspace 归属租户
│   ├── models/                       # ORM 表
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── workspace.py
│   │   ├── conversation.py
│   │   ├── asset.py
│   │   ├── knowledge.py
│   │   ├── job.py
│   │   └── quota.py
│   ├── schemas/                      # Pydantic 请求/响应
│   │   └── ...
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── workspaces.py
│   │       ├── conversations.py      # 含 SSE
│   │       ├── knowledge.py          # 含 search / search/image
│   │       ├── assets.py
│   │       ├── jobs.py
│   │       └── settings.py
│   ├── services/                     # 应用服务（编排用例）
│   │   ├── agent/                    # Pydantic AI + Harness
│   │   │   ├── factory.py            # 组装 Agent(model, capabilities, deps)
│   │   │   ├── deps.py               # PrismDeps（tenant/workspace/db…）
│   │   │   ├── instructions.py       # 系统提示（中文产品语气）
│   │   │   ├── streaming.py          # run_stream → SSE 事件映射
│   │   │   └── capabilities/         # 自研 + 选用的 harness 能力
│   │   │       ├── media_gen.py      # 生图/生视频 tools
│   │   │       ├── knowledge_rag.py  # 文本检索 / 图搜
│   │   │       ├── publish.py        # Phase 2 占位
│   │   │       └── ads.py            # Phase 3 占位
│   │   ├── media/
│   │   │   ├── gateway.py
│   │   │   └── providers/            # 各模型供应商适配
│   │   ├── knowledge/
│   │   │   ├── ingest.py
│   │   │   ├── search_text.py
│   │   │   ├── search_image.py
│   │   │   └── segments.py           # Phase 2 占位
│   │   ├── assets/
│   │   ├── publish/                  # Phase 2 占位
│   │   └── ads/                      # Phase 3 占位
│   ├── jobs/                         # 队列任务定义
│   │   ├── generate_image.py
│   │   ├── generate_video.py
│   │   └── ingest_document.py
│   └── tests/
│       ├── unit/
│       └── integration/              # 含串租隔离用例
└── Dockerfile
```

**约定**

- `api/` 只做参数校验与鉴权，业务进 `services/`。
- 所有查询带 `tenant_id`；空间资源再带 `workspace_id`。
- Provider、Publish、Ads 一律 **Adapter 接口**，便于换供应商。

---

## 4. 基础设施 `infra`

```
infra/
├── docker-compose.yml        # postgres(+pgvector) · redis · minio · api · worker · web(可选)
├── postgres/init.sql
└── deploy/
    └── README.md             # 云部署备忘（厂商选定后补）
```

---

## 5. 请求上下文（前后端对齐）

```
Authorization: Bearer <jwt>
X-Tenant-Id:   <可选，若 jwt 已含则以 jwt 为准>
X-Workspace-Id: <除工作空间列表/租户设置外必填>
```

JWT claims 建议：`sub`（user_id）、`tenant_id`、`role`。

---

## 6. MVP 先实现的包（最小集）

**前端页面**：workspaces · 工作台 · chat · knowledge · assets · settings（骨架）  
**后端路由**：auth · workspaces · conversations · knowledge · assets · jobs · settings/providers  
**可延后建文件**：`services/publish` · `services/ads` · `segments` 实现（仅占位即可）

---

## 7. 本地启动（目标形态）

```bash
# 依赖
docker compose -f infra/docker-compose.yml up -d

# 后端
cd apps/api && uv sync && uv run uvicorn app.main:app --reload
uv run python -m app.worker

# 前端
cd apps/web && pnpm install && pnpm dev
```

具体命令在脚手架落地时写入根 `README.md`。
