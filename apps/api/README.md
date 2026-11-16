# Prism API

FastAPI 后端：多租户鉴权、对话 Agent、Media Gateway（生图/生视频）、知识库检索、资产与租户级模型配置。

| | |
|---|---|
| **开发者** | [jintao](https://github.com/jintao0693) |
| **默认端口** | `8000` |
| **OpenAPI** | http://127.0.0.1:8000/docs |

---

## 功能概览

- **Auth**：邮箱密码登录，JWT；业务请求需 `Authorization` + `X-Workspace-Id`
- **Workspaces**：租户下工作空间列表 / 详情
- **Conversations**：会话与消息；SSE 流式回复；可触发生图/生视频任务
- **Knowledge**：知识库文档入库、文本检索、图搜图（多模态 embedding）
- **Assets / Jobs**：素材与异步任务状态
- **Settings**：火山方舟 Provider 读写与连通测试

未配置真实模型时走 **演示模式**（本地启发式回复 + Demo Provider），便于无 Key 联调前端。

---

## 快速开始

```bash
cd apps/api
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -e .
# 可选：真实 Pydantic AI 工具循环
# pip install -e ".[agent]"

copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

| 检查项 | 地址 |
|--------|------|
| Swagger | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |

### 演示账号

| 字段 | 值 |
|------|-----|
| 邮箱 | `linqing@prism.demo` |
| 密码 | `prism123` |
| 工作空间 | `ws_spring`（种子数据） |

```http
Authorization: Bearer <access_token>
X-Workspace-Id: ws_spring
```

---

## 环境变量（要点）

见 `.env.example`：

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 默认 SQLite；生产用 `postgresql+asyncpg://...` |
| `REDIS_URL` | 可选；无 Redis 时任务可走进程内 |
| `SECRET_KEY` | JWT / 加密相关密钥，生产必须更换 |
| `AGENT_DEMO_MODE` | `true` 时强制演示；火山启用后对话仍可走方舟 |
| `CORS_ORIGINS` | 默认包含 `http://localhost:3000` |
| `STORAGE_BACKEND` | `local` 或 S3 兼容 |

租户级火山 Key **不写在 .env**，写在设置 API / 前端设置页（库内加密存储）。

---

## 火山方舟接入

Base URL：`https://ark.cn-beijing.volces.com/api/v3`

| 能力 | 接口形态 | 配置字段 |
|------|----------|----------|
| 对话 | `POST .../chat/completions` | `chatModel` |
| 生图 | `POST .../images/generations` | `imageModel`（Seedream） |
| 生视频 | 异步 contents/generations 任务 | `videoModel`（Seedance） |
| 向量 | `POST .../embeddings/multimodal` | `embeddingModel` |

HTTP：

- `GET /api/v1/settings/providers/volcengine`
- `PUT /api/v1/settings/providers/volcengine`
- `POST /api/v1/settings/providers/volcengine/test`（对话连通）

启用条件：`enabled=true` 且已保存有效 API Key。模型 ID 须为控制台已开通的 Model / Endpoint ID。

实现位置：

- `app/services/providers/volcengine/client.py` — HTTP 客户端  
- `app/services/media/providers/volcengine.py` — Media Provider  
- `app/services/providers/registry.py` — 租户配置加载  

---

## 目录说明

| 路径 | 说明 |
|------|------|
| `app/api/v1/` | 路由：auth / workspaces / conversations / knowledge / assets / jobs / settings |
| `app/services/agent/` | Agent factory、SSE、capabilities、demo_runner |
| `app/services/media/` | MediaGateway + demo / volcengine Provider |
| `app/services/knowledge/` | 入库、文本/图像检索、embedding 工具 |
| `app/services/providers/` | 供应商注册与火山客户端 |
| `app/models/` | SQLAlchemy ORM（含 `provider_config`） |
| `app/schemas/` | Pydantic 请求/响应 |
| `app/core/` | 配置、DB、JWT、加密、存储 |
| `app/bootstrap/seed.py` | 演示租户 / 用户 / 工作空间 |
| `app/jobs/` | 生图、生视频、文档入库任务 |

---

## Agent 行为

1. 租户已启用火山 + Key → 对话优先方舟 Chat；工具侧生图/视频走 MediaGateway  
2. 未配置 → `demo_runner` + Demo Media Provider  
3. `AGENT_DEMO_MODE=false` 且安装 `.[agent]` → 可走 Pydantic AI 工具循环（实验）

---

## 可选基础设施

```bash
docker compose -f ../../infra/docker-compose.yml up -d
```

把 `DATABASE_URL` 改为 Postgres 后重启 API。

---

## 开发者

维护者：**jintao**（[@jintao0693](https://github.com/jintao0693)）  
许可：与仓库根目录 MIT 一致。
