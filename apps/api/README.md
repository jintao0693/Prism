# Prism API

FastAPI + SQLAlchemy + **Pydantic AI Harness 形态**（演示模式默认不调外网模型）。

## 快速开始

```bash
cd apps/api
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -e .
copy .env.example .env

uvicorn app.main:app --reload --port 8000
```

打开文档：http://localhost:8000/docs  
健康检查：http://localhost:8000/health

### 演示账号

- 邮箱：`linqing@prism.demo`
- 密码：`prism123`

登录后请求业务接口需带：

```http
Authorization: Bearer <token>
X-Workspace-Id: ws_spring
```

## 目录要点

| 路径 | 说明 |
|------|------|
| `app/api/v1` | HTTP 路由 |
| `app/services/agent` | Agent factory / SSE / 自研 capabilities |
| `app/services/media` | 生图生视频网关与 Provider |
| `app/services/knowledge` | 检索与入库 |
| `app/models` | ORM |
| `app/bootstrap/seed.py` | 演示种子数据 |

## 火山方舟（优先）

在前端 **设置** 页或 `PUT /api/v1/settings/providers/volcengine` 配置：

| 字段 | 说明 |
|------|------|
| API Key | 方舟控制台 Key |
| chatModel | 对话模型 / Endpoint ID |
| imageModel | Seedream 生图 |
| videoModel | Seedance 视频（异步任务） |
| embeddingModel | 多模态向量（图搜 / 文本检索） |

启用后：对话走方舟 Chat；生图/生视频走对应 API；知识库检索走 `/embeddings/multimodal`。

## Agent 模式

- 已配置火山：优先火山链路
- 未配置：本地启发式 + Demo Provider
- `AGENT_DEMO_MODE=false` 且安装 `.[agent]`：可走 Pydantic AI 工具循环

## 可选基础设施

```bash
docker compose -f ../../infra/docker-compose.yml up -d
```

然后将 `.env` 中 `DATABASE_URL` 改为 Postgres。
