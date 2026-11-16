# Prism 技术文档

> 版本：v0.1  
> 作者 / 开发者：**jintao**（[@jintao0693](https://github.com/jintao0693)）  
> 对应产品文档：`docs/PRODUCT.md`  
> 原则：参考开源能力与流程，自建多租户云端底座；不 fork bony-agent 等整仓。

---

## 1. 目标与约束

| 项 | 决策 |
|----|------|
| 部署形态 | 云端多租户 SaaS |
| MVP | 对话驱动生图/生视频 + 简单知识库（含图搜图） |
| 全量目标 | 社媒矩阵发布 + 巨量/Meta 付费投放 + 视频片段检索 |
| 设计协作 | 产品/技术文档先行 → 确认页面 IA → 再出界面稿 |

---

## 2. 总体架构

```
                    ┌─────────────────────────────────────┐
                    │           API Gateway / BFF          │
                    │      Auth · Tenant Context · RL      │
                    └───────────────┬─────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ Agent Service │         │  Knowledge Svc  │         │   Asset Svc     │
│ 对话·工具编排  │         │ 入库·检索·多模态 │         │ 元数据·血缘      │
└───────┬───────┘         └────────┬────────┘         └────────┬────────┘
        │                          │                           │
        ▼                          ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ Media Gateway │         │ Vector / Search │         │ Object Storage  │
│ 图/视频供应商  │         │ 文本+图像+片段   │         │ 租户前缀隔离     │
└───────────────┘         └─────────────────┘         └─────────────────┘

Phase 2+: Publish Svc（社媒）  Phase 3+: Ads Svc（巨量/Meta）
横切：Identity & Tenancy · Billing/Quota · Audit · Job Queue · Observability
```

**设计要点**

- **租户上下文**贯穿所有服务（`tenant_id` 强制注入，禁止跨租户查询）。
- **生成与检索解耦**：Media Gateway 可换模型；Knowledge 独立演进到视频片段。
- **异步任务**：生视频、视频切段、发布、投放同步走队列，对话侧轮询/SSE。

---

## 3. 推荐技术选型（可调整）

| 层 | 建议 | 说明 |
|----|------|------|
| 前端 | Next.js (App Router) + TypeScript | 多租户控制台；SSR/CSR 混合 |
| BFF / API | FastAPI | 与 Pydantic AI 同栈 |
| Agent 编排 | **Pydantic AI + Pydantic AI Harness** | 见 §5.1；以 harness / capabilities 为主轴 |
| 主库 | PostgreSQL | 租户、用户、会话、任务、资产元数据 |
| 向量 / 检索 | pgvector（MVP）→ 后期可迁 Milvus/Qdrant | 文本 + 图像向量；片段向量同库不同 collection/表 |
| 对象存储 | S3 兼容（OSS / MinIO / R2） | `s3://{bucket}/{tenant_id}/...` |
| 队列 | Redis + RQ/Celery 或 Cloud Tasks | 生成、切段、发布 |
| 鉴权 | Clerk / Auth0 / 自建 OIDC | 组织 = 租户；JWT 含 `tenant_id` + `role` |
| 观测 | OpenTelemetry + Loki/Sentry | 按租户维度打点 |

> 仓库已落地为 Monorepo：`apps/web`（Next.js）+ `apps/api`（FastAPI）；火山方舟 Chat / Seedream / Seedance / Embedding 已接入租户级配置。

---

## 4. 多租户模型

### 4.1 隔离级别（MVP）

- **逻辑隔离**：共享集群与数据库，所有业务表带 `tenant_id`，行级强制过滤。
- **存储隔离**：对象存储按租户前缀；签名 URL 短时有效。
- **密钥隔离**：模型 Key、社媒 Token、广告 Token 均租户级加密存储（KMS 或应用层 AES + 主密钥）。

### 4.2 核心实体（简表）

```
Tenant
User ↔ Membership(tenant_id, role)
Workspace（必需：租户下多工作空间）
Conversation / Message（归属 workspace_id）
GenerationJob
Asset
KnowledgeBase / KnowledgeItem
EmbeddingRef（指向向量库 id）
ChannelCredential（Phase 2/3）
PublishJob / AdsDraft（Phase 2/3）
QuotaUsage
AuditLog
```

### 4.3 权限

- API 中间件：解析 JWT → 校验 membership → 注入 `TenantContext`。
- 知识库/资产所有查询：`WHERE tenant_id = :ctx`。
- 管理接口：仅 Owner/Admin。

---

## 5. 模块设计

### 5.1 Agent Service（MVP 核心）— Pydantic AI Harness

**已选定**：以 **Pydantic AI** 为 agent 循环，以 **Pydantic AI Harness** 的 capability 组合为扩展层（官方用语里的 harness）。

| 层 | 包 | 在 Prism 中的用法 |
|----|-----|-------------------|
| Core | `pydantic-ai` | `Agent` 循环、模型路由、流式、结构化输出、自有 tools |
| Harness | `pydantic-ai-harness` | 按需挂载 memory / context / sub-agents / guardrails 等官方 capability |
| Prism 自研 | `app/services/agent/capabilities/` | 生图、生视频、知识库检索、图搜图、（后期）发布/投放 |

**形态**

- 对外仍是对话产品：普通问题 → **纯文本答案**（可不调任何工具）。
- 对内是 harness：把「媒体生成 / 知识库 / 投放」做成可插拔 **capabilities**，挂到同一个 `Agent(..., capabilities=[...])`。
- 不默认上 Coder（写代码/shell）全量栈；只取我们需要的官方块 + 自研媒体能力。
- 不用 LangGraph 作为主编排（避免双框架）；复杂多步后期可用 SubAgents capability。

**示意（实现阶段）**

```python
from pydantic_ai import Agent
# from pydantic_ai_harness... 按需引入 memory / context 等
from app.services.agent.capabilities import MediaGen, KnowledgeRAG

agent = Agent(
    model=tenant_model,           # 租户可配置
    deps_type=PrismDeps,          # tenant_id, workspace_id, db, storage...
    instructions=PRISM_SYSTEM,
    capabilities=[MediaGen(), KnowledgeRAG()],
)
# 简单问答：无 tool → 文本流
# 创作意图：capability 工具 → 再总结
```

**一次请求**

```
用户消息
  → Pydantic AI agent.run / run_stream
  → 无工具：纯文本 SSE
  → 有工具：Media / KB capability → 结果回灌 → 文本+卡片
  → SSE：text.delta | tool.start | tool.result | message.done
```

**MVP 能力（自研 capability / tools）**

| Tool / Capability | 输入 | 输出 |
|-------------------|------|------|
| `text_to_image` | prompt, size, refs? | asset_id |
| `image_to_image` | image_asset_id, prompt | asset_id |
| `text_to_video` | prompt, duration, ratio | job_id → asset_id |
| `image_to_video` | image_asset_id, prompt | job_id → asset_id |
| `kb_search_text` | query, kb_ids | chunks |
| `kb_search_image` | image_asset_id / upload, kb_ids | similar images |

**交互**：FastAPI SSE 桥接 Pydantic AI 流式事件。

### 5.2 Media Gateway

- 统一抽象：`Provider` 接口（OpenAI 兼容、通义、可灵、Seedream/Seedance、自建 Comfy 等）。
- 租户路由：租户配置默认供应商与模型；无配置则用平台默认（计费另议）。
- 产物：下载到对象存储 → 写 `Asset` → 返回内部 URL。

### 5.3 Knowledge Service

#### MVP

| 能力 | 实现要点 |
|------|----------|
| 文档入库 | 解析 → chunk → 文本 embedding → pgvector |
| 图片入库 | 存原图 → **图像 embedding**（如 CLIP / 多模态 embedding API）→ 向量表 |
| 文本问答 | 向量召回 + 可选 rerank + LLM 生成 |
| 图搜图 | query 图 embedding → 近邻搜索 → 返回 Asset/KnowledgeItem |

#### Phase 2：视频片段检索（架构预留）

```
Video upload
  → 转码/标准化
  → 按镜头或固定窗切段（如 2–5s，可重叠）
  → 每段：关键帧图像 embedding + ASR 文本 embedding
  → 索引：segment_id, asset_id, t_start, t_end, vectors
  → 检索：图/文 query → TopK segments → 播放器 seek
```

表/集合建议：`kb_segments(tenant_id, asset_id, t_start, t_end, ...)`，与图片向量分表，避免 MVP 污染。

### 5.4 Asset Service

- 元数据、标签、集合、简版血缘（`source_conversation_id`, `source_job_id`）。
- 预览：图片直链；视频 HLS/MP4 渐进（MVP 可用原文件）。
- 删除：软删 + 存储生命周期策略。

### 5.5 Publish Service（Phase 2）

- 适配器模式：`XiaohongshuAdapter` / `DouyinAdapter` / …
- 优先官方开放平台；无开放能力再评估 RPA（风控高，不进核心路径默认）。
- 任务状态机：`draft → scheduled → publishing → succeeded|failed`。

### 5.6 Ads Service（Phase 3）

- 适配器：`OceanEngineAdapter` / `MetaMarketingAdapter`。
- MVP 投放阶段范围：**OAuth、素材上传、草稿创建、报表拉取**；不做智能出价。
- 与 Asset 双向关联：`ads_creative_link(asset_id, external_ad_id, metrics_json)`。

---

## 6. API 草图（MVP）

> 前缀：`/api/v1`；均需鉴权；隐式租户。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/...` | 登录/邀请（视 IdP） |
| GET/POST | `/conversations` | 会话列表/创建 |
| POST | `/conversations/{id}/messages` | 发消息（SSE） |
| GET/POST | `/knowledge-bases` | 知识库 |
| POST | `/knowledge-bases/{id}/documents` | 上传文档 |
| POST | `/knowledge-bases/{id}/images` | 上传图片 |
| POST | `/knowledge-bases/{id}/search` | 文本检索 |
| POST | `/knowledge-bases/{id}/search/image` | 图搜图 |
| GET | `/assets` | 资产列表 |
| GET | `/assets/{id}` | 详情 |
| GET/PUT | `/settings/providers` | 模型供应商配置 |
| GET | `/jobs/{id}` | 异步任务状态 |

Phase 2/3 另增 `/publish/*`、`/ads/*`。

---

## 7. 数据流（MVP 关键路径）

### 7.1 对话生图

```
Client → POST message
  → Agent: 可选 kb_search_*
  → Agent: text_to_image
  → Media Gateway → Provider
  → 存 OSS + Asset
  → SSE 推送结果卡片
```

### 7.2 图搜图

```
Client → POST search/image (file 或 asset_id)
  → 图像 embedding
  → 向量 TopK（tenant + kb 过滤）
  → 返回缩略图与 metadata
```

---

## 8. 安全与合规

| 项 | 做法 |
|----|------|
| 租户隔离 | 中间件强制；集成测试覆盖串租用例 |
| 密钥 | 加密存储；前端永不回显明文 |
| 上传 | 类型/大小限制；病毒扫描可后期 |
| 签名 URL | 短 TTL；下载审计 |
| 广告/发布 Token | 按租户、按平台分库字段；支持吊销 |
| Prompt 注入 | 系统提示与工具结果隔离；知识库内容不当作指令 |

---

## 9. 配额与计费（骨架）

- 表：`quota_limits` / `quota_usage`（生成次数、存储 GB、坐席）。
- MVP：硬限额 + 管理台展示用量；支付与套餐可后置。

---

## 10. 部署拓扑（建议）

```
CDN → Web (Vercel/自建)
    → API (容器 / Cloud Run / K8s)
    → Worker (同镜像不同 cmd)
    → Postgres + Redis
    → S3
```

环境：`dev` / `staging` / `prod`；每租户无独立集群（成本过高），用逻辑隔离。

---

## 11. 与开源项目的关系

| 项目 | 用法 |
|------|------|
| bony-agent | 参考 Agent 分工与发布叙事；不作为依赖 |
| MoneyPrinterTurbo | 参考短视频流水线步骤拆分 |
| Dify / RAGFlow | 参考知识库产品交互与入库流水线；MVP 自研轻量实现 |
| CLIP/多模态 embedding 方案 | 图搜图、片段关键帧向量的技术基础 |

**禁止**：把 Playwright 大规模平台发布作为 SaaS 默认实现；优先官方 API。

---

## 12. 里程碑（工程）

| 里程碑 | 交付 |
|--------|------|
| M0 | 本产品/技术文档确认 + 页面 IA 确认 |
| M1 | 多租户骨架 + 登录 + 空壳控制台 |
| M2 | 对话 + 生图/生视频网关 + 资产库 |
| M3 | 知识库文档检索 + 图搜图 |
| M4 | 视频切段检索 |
| M5 | 社媒发布适配器（首批 1–2 平台） |
| M6 | 巨量/Meta 草稿 + 报表 |

---

## 13. 页面实现协作说明

| 方式 | 当前能力 |
|------|----------|
| **Figma** | 本会话**未接入 Figma MCP/插件**，无法直接读写你的 Figma 文件。你可：装官方 Figma 桌面端 + Cursor Figma 相关插件后授权；或导出/分享文件，我按节点规范出标注与组件说明。 |
| **Pencil（`.pen`）** | Cursor 侧可用 Pencil 技能直接出界面稿并迭代，适合文档确认后快速定页面。 |
| **文档线框** | 可先在 `docs/IA.md` 把每页区块与关键状态写清，再进任一设计工具。 |

---

## 14. 产品侧已锁定（同步）

- 品牌 Prism；中文 UI；Workspace 必需；视频片段检索 Phase 2。

## 15. 推荐默认（可直接采纳，有异议再说）

| 项 | 推荐默认 | 说明 |
|----|----------|------|
| 仓库 | **Monorepo** | 见 `docs/STRUCTURE.md` |
| 前端 | **Next.js（App Router）+ TypeScript**（已选定） | `apps/web`；业务在 FastAPI，前端不写核心 Agent 逻辑 |
| 后端 | **Python FastAPI** | `apps/api` |
| Agent | **Pydantic AI + Pydantic AI Harness** | 自研 Media/KB capabilities；按需挂官方 memory/context 等 |
| 鉴权 MVP | **自建邮箱+密码 / JWT** | 后期可换 Clerk/Auth0；表结构预留 `auth_provider` |
| 图搜 embedding | **云 API 多模态 embedding** | 自托管 CLIP 作备选，接口层抽象 |
| 向量库 | **Postgres + pgvector** | |
| 对象存储本地 | **MinIO** | 生产再换 OSS/S3 |
| 云厂商 | **先不绑死** | Docker Compose 本地可跑即可 |

## 16. 仍不清楚 / 建议你拍板

### 阻塞脚手架的（建议开工前定）

1. **是否采纳上文「推荐默认」整包？**（尤其 FastAPI + Next.js + 自建 JWT）  
2. **登录方式**：仅邮箱密码，还是还要手机号 / 微信扫码（微信可后置）？

### 不阻塞 MVP、但迟早要定

3. 社媒首批平台顺序（小红书 / 抖音 / 视频号 / …）  
4. 投放首发：巨量 / Meta / 双线  
5. 生产云厂商（阿里云 / AWS / 其他）与域名  
6. 生图/生视频**首发供应商**（通义、可灵、OpenAI 兼容中转等）——可做成可配置，但要有一个默认联调对象  
7. 空间角色：是否与租户角色分离（MVP 可先「空间成员 = 租户成员可见该空间」）

### 已清楚、无需再问

- 品牌 Prism、中文 UI、Workspace、MVP 范围、图搜图要做、片段检索预留、HTML 草稿可接受、目录结构见 STRUCTURE.md

---

## 17. 文档状态

- [x] 目录结构已写清（`docs/STRUCTURE.md`）  
- [ ] 技术默认项用户确认  
- [x] MVP 接口范围已在本文 §6 列出  
- [x] 产品关键决策已对齐  
