# Prism 开发进度

> 维护者：**jintao**（[@jintao0693](https://github.com/jintao0693)）  
> 仓库：https://github.com/jintao0693/Prism  
> 更新：2026-11-16

本文是「做到哪了 / 下一步做什么 / 卡在哪」的单一事实来源。产品愿景见 [PRODUCT.md](PRODUCT.md)，路线图见 [../ROADMAP.md](../ROADMAP.md)。

---

## 1. 总览

| 维度 | 状态 | 说明 |
|------|------|------|
| 产品 MVP 骨架 | ✅ 基本完成 | 登录、工作空间、对话、知识库、资产、设置页 |
| 前后端联调 | ✅ 已接通 | 登录→工作空间→对话 SSE→知识库/资产/设置 |
| 意图识别 | ✅ 已上线 | 对话模型分类 chat/image/video/knowledge，失败回退正则 |
| 多模态知识库 | 🔄 半成品 | 文本检索/以文搜图可用；上传文件、真·以图搜图、片段检索未做 |
| 页面表达 | 🔄 已纠偏 | 去掉假上传/夸大文案；对话显示意图进度并可勾选知识库 |
| 火山方舟接入 | ✅ 代码完成 | Chat / Seedream / Seedance / Embedding；需自备 Key 验收 |
| 开源基建 | ✅ 完成 | MIT、AUTHORS、CI、Issue/PR 模板、CONTRIBUTING 等 |
| 首跑可用性 | ✅ 已合入 | CORS、密码盐、SSR URL、mock 默认值已推 main |
| 测试 | 🔄 加厚中 | health/login/security/settings 共 6 测通过；media 待补 |
| Docker 全栈 | 🔄 半完成 | `--profile full` + SSR `API_BASE_URL` 已配；待实机验收 |
| Alembic | ❌ 未做 | 仍用 `create_all` |
| Phase 2/3 | ❌ 未做 | 视频片段、社媒、投放 |

---

## 2. 已完成（按模块）

### 2.1 前端 `apps/web`

- [x] Next.js 15 App Router + 中文 UI 壳（Topbar / Sidebar / Workspace）
- [x] 页面：登录、工作空间、工作台、对话、知识库、资产、设置
- [x] 真实 API 客户端（JWT cookie + `X-Workspace-Id`）
- [x] 设置页：火山方舟 Key / 四类模型 / 启用 / 连通测试
- [x] `USE_MOCK` 仅当显式 `true`；默认走真实后端
- [x] SSR 可走 `API_BASE_URL`（Docker 内 `http://api:8000`）

### 2.2 后端 `apps/api`

- [x] FastAPI + SQLAlchemy 异步 + 演示种子数据
- [x] 鉴权 JWT；租户 / 工作空间隔离头
- [x] Agent 演示模式 + 火山 Chat 优先
- [x] Media Gateway：Demo / Volcengine（生图、生视频）
- [x] 知识库入库 / 文本检索 / 图搜（multimodal embedding）
- [x] 租户级 Provider 配置（Key 加密存储）
- [x] 密码哈希改为随机 salt（不绑 `SECRET_KEY`）；演示账号可自动修哈希
- [x] CORS 默认含 `localhost` 与 `127.0.0.1`

### 2.3 开源与工程

- [x] 公开仓库 + MIT + AUTHORS（jintao）
- [x] README / docs / ROADMAP / CHANGELOG / SECURITY / CONTRIBUTING / CoC
- [x] GitHub Actions CI（ruff + pytest + web lint/build）
- [x] `scripts/dev.ps1` / `dev.sh`
- [x] Compose：依赖服务 + `--profile full`（api/web）

---

## 3. 进行中 / 待验证

| 项 | 说明 | 是否需要你 |
|----|------|------------|
| P0 可用性修复合入 | 密码盐、CORS、mock 默认、Docker SSR URL | 否（代码侧） |
| 扩大自动化测试 | auth / settings / security 单测 | 否 |
| 火山真机联调 | 填方舟 Key，测对话/生图/视频/向量 | **是**（需要你的 API Key 与已开通模型 ID） |
| Docker `--profile full` 实机 | 本机 Docker 拉起全栈点一遍 | **可选**（有 Docker 时） |

---

## 4. 下一步（建议顺序）

### Now（本周继续）

1. ~~进度文档~~ → 本文  
2. 合入 P0 修复 + 补充测试并推送  
3. Alembic 初始迁移（替代纯 `create_all`）  
4. 联调体验：任务进度、错误文案、空状态  
5. README 加截图 / 演示 GIF（**需要你**：本地跑通后截几张，或授权我用浏览器截）

### Next（Phase 2 前）

- 配额真实计量  
- Worker / 队列从占位变为可选消费  
- 更深健康检查（DB / Redis）  
- pre-commit / dependabot  

### Later

- 视频片段检索、社媒发布、巨量/Meta — 见 ROADMAP  

---

## 5. 本地怎么验收（当前）

```bash
# 准备
.\scripts\dev.ps1          # 或 ./scripts/dev.sh

# 终端 1
cd apps/api
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# 终端 2
cd apps/web
npm run dev
```

- 打开 http://127.0.0.1:3000  
- 账号：`linqing@prism.demo` / `prism123`  
- 设置页填火山 Key 后测连通（可选）  

自动化：

```bash
cd apps/api
python -m ruff check app
python -m pytest -q
```

---

## 6. 已知坑（给贡献者）

| 坑 | 处理 |
|----|------|
| 改过旧版 `SECRET_KEY` 后登录失败 | 启动时会尝试重哈希演示账号；仍不行可删 `apps/api/data/*.db` 重种子 |
| 前端像「假数据」 | 确认 `.env.local` 里 `NEXT_PUBLIC_USE_MOCK` 不是 `true` |
| Docker 全栈 SSR 调不通 | Web 容器需 `API_BASE_URL=http://api:8000/api/v1`，浏览器侧仍用 `localhost:8000` |
| Makefile 在 Windows | 优先用 `scripts/dev.ps1`；Makefile 面向 Unix |
| Worker | `app/worker.py` 仍为占位，任务目前偏进程内 |

---

## 7. 变更与文档索引

| 文档 | 用途 |
|------|------|
| [PROGRESS.md](PROGRESS.md) | **当前进度（本文）** |
| [../ROADMAP.md](../ROADMAP.md) | 中长期里程碑 |
| [../CHANGELOG.md](../CHANGELOG.md) | 已发布变更 |
| [PRODUCT.md](PRODUCT.md) | 产品范围 |
| [TECHNICAL.md](TECHNICAL.md) | 架构 |
| [STRUCTURE.md](STRUCTURE.md) | 目录约定 |
