# Prism

**多租户 SaaS 多模态 Agent 平台** — 用对话完成品牌知识检索、图片/视频生成、素材归档；后续覆盖社媒矩阵发布与付费投放（巨量 / Meta）。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](apps/api)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](apps/web)

| | |
|---|---|
| **开发者** | [jintao](https://github.com/jintao0693)（`jintao0693`） |
| **仓库** | https://github.com/jintao0693/Prism |
| **状态** | MVP 进行中（对话 / 知识库 / 资产 / 火山方舟已接通） |
| **许可** | MIT |

---

## 产品简介

Prism 面向营销与内容团队，把「查品牌知识 → 出图出片 → 管素材 →（后续）发社媒 / 投广告」收进同一套多租户控制台：

1. **创作对话**：自然语言驱动文本问答、Seedream 生图、Seedance 生视频  
2. **知识库**：文档 / 图片入库，文本问答 + 多模态向量图搜图（视频片段检索为 Phase 2）  
3. **资产中心**：生成结果与上传素材统一归档、预览、打标  
4. **租户设置**：火山方舟（字节）API Key 与模型 ID 租户级隔离配置  

详细产品说明见 [docs/PRODUCT.md](docs/PRODUCT.md)。

---

## 功能一览（当前）

| 模块 | 能力 | 说明 |
|------|------|------|
| 账号 / 租户 | 登录、工作空间隔离 | JWT + `X-Workspace-Id` |
| 对话 Agent | 文本问答、生图、生视频 | 有火山 Key 走方舟，否则演示模式 |
| 知识库 | 上传、文本检索、图搜图 | 向量走方舟 multimodal embedding |
| 资产 | 列表 / 预览 / 标签 | 与生成任务联动 |
| 设置 | 火山方舟配置、连通测试 | 对话 / 生图 / 视频 / 向量四类模型 |
| 基础设施 | Docker Compose | Postgres / Redis / MinIO（可选） |

**规划中**：视频片段检索、社媒发布、巨量 / Meta 投放 — 见产品文档 Phase 2 / 3。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 15（App Router）+ TypeScript |
| 后端 | FastAPI + SQLAlchemy（异步）+ Pydantic |
| Agent | Pydantic AI Harness 形态（可选 extras） |
| 模型 | 火山方舟 Ark：Chat / Seedream / Seedance / Embedding Vision |
| 数据 | 默认 SQLite；生产建议 PostgreSQL + pgvector |
| 队列 / 缓存 | Redis（可选） |
| 存储 | 本地目录或 S3 兼容（MinIO） |

更多架构说明见 [docs/TECHNICAL.md](docs/TECHNICAL.md)、[docs/STRUCTURE.md](docs/STRUCTURE.md)。

---

## 仓库结构

```
Prism/
├── apps/
│   ├── web/          # Next.js 前端控制台
│   └── api/          # FastAPI 后端 + Agent / Media / Knowledge
├── design/prism-ui/  # 界面 HTML 草稿
├── docs/             # 产品 / 技术 / IA / 目录结构
├── infra/            # docker-compose（Postgres / Redis / MinIO）
├── LICENSE
└── README.md
```

---

## 快速开始

### 环境要求

- Node.js 20+
- Python 3.11+
- （可选）Docker：跑 Postgres / Redis / MinIO

### 1. 启动后端

```bash
cd apps/api
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -e .
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API 文档：http://127.0.0.1:8000/docs  
- 健康检查：http://127.0.0.1:8000/health  

**演示账号**

| 字段 | 值 |
|------|-----|
| 邮箱 | `linqing@prism.demo` |
| 密码 | `prism123` |
| 工作空间示例 | `ws_spring` |

### 2. 启动前端

```bash
cd apps/web
npm install
```

创建 `apps/web/.env.local`（可参考 `.env.example`）：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_USE_MOCK=false
```

```bash
npm run dev
```

打开 http://localhost:3000 → 登录 → 选择工作空间 → **设置** 中配置火山方舟。

### 3.（可选）基础设施

```bash
docker compose -f infra/docker-compose.yml up -d
```

然后将 `apps/api/.env` 里的 `DATABASE_URL` 改为 Postgres 连接串。

---

## 火山方舟（字节）接入

在控制台 **设置** 页填写，或调用：

`PUT /api/v1/settings/providers/volcengine`

| 配置项 | 用途 | Ark 能力 |
|--------|------|----------|
| API Key | 鉴权 | — |
| chatModel | 对话 | `/chat/completions` |
| imageModel | 生图 | Seedream `/images/generations` |
| videoModel | 生视频 | Seedance 异步任务 |
| embeddingModel | 向量 | `/embeddings/multimodal` |

启用且 Key 有效后：对话 / 生图 / 生视频 / 知识库检索优先走火山；否则回退演示 Provider。  
模型 ID 请换成你在[火山方舟控制台](https://console.volcengine.com/ark)已开通的 Model / Endpoint ID。

后端细节：[apps/api/README.md](apps/api/README.md)

---

## 文档索引

| 文档 | 内容 |
|------|------|
| [docs/PRODUCT.md](docs/PRODUCT.md) | 产品定位、用户、MVP / Phase 范围、旅程 |
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | 架构、租户模型、Agent、Media、检索、安全 |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | Monorepo 目录与分包约定 |
| [docs/IA.md](docs/IA.md) | 页面信息架构 |
| [apps/web/README.md](apps/web/README.md) | 前端开发说明 |
| [apps/api/README.md](apps/api/README.md) | 后端开发与火山配置 |
| `design/prism-ui/index.html` | 界面视觉草稿 |

---

## 开发者

本项目由 **jintao**（GitHub [@jintao0693](https://github.com/jintao0693)）设计与开发维护。

欢迎 Issue / PR。建议先读产品与技术文档，再改对应 `apps/web` 或 `apps/api` 模块。

---

## License

[MIT](LICENSE) © jintao
