# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 风格。

## [Unreleased]

### Added

- 多模态 Agent 统一 `tool_runner`：文/图生图、文/图生视频、KB 检索；资产记忆与 `parentAssetId` 血缘
- 对话多轮上下文：滑动窗 + 摘要检查点；usage 触发自动压缩；手动 `POST .../compact`
- 多模态知识库：图片入库/检索/以图搜图、补齐向量、批量上传；Postgres pgvector / SQLite JSON 双路径
- SSE 真流式 + 视频 `media.progress`；图生视频失败时回传可读错误事件
- 游戏向联调：`scripts/run_game_cases.py` + `docs/GAME_CASES.md`（KB / T2I→I2I / I2V 三案例）
- `docs/PROGRESS.md` 开发进度单一事实来源
- 开源协作文档：CONTRIBUTING、CODE_OF_CONDUCT、SECURITY、ROADMAP
- GitHub Actions CI（API ruff/pytest、Web lint/build）
- `scripts/dev.ps1` / `scripts/dev.sh` 本地启动脚本
- API 冒烟测试（health / login）
- MIT License 与 AUTHORS（维护者 jintao）
- Docker Compose `--profile full`（api + web）与 API healthcheck
- 密码哈希随机 salt；演示账号自动修哈希
- API 测试：security / volcengine settings；`/health` 探测数据库；context / tool_select

### Changed

- CORS 默认同时允许 `localhost:3000` 与 `127.0.0.1:3000`
- 前端 `USE_MOCK` 仅当显式 `true`；SSR 可用 `API_BASE_URL`
- 根 README 与 apps 文档细化；产品/技术文档标注作者 jintao
- `docs/STRUCTURE.md` 与仓库实际目录对齐
- 图生视频首帧任务不再传 `ratio`（跟随首帧图比例，避免方舟 400）

## [0.1.0] - 2026-11-16

### Added

- Monorepo：Next.js 前端 + FastAPI 后端
- 演示租户种子数据与登录
- 火山方舟：对话 / Seedream / Seedance / multimodal embedding
- 知识库、资产中心、设置页骨架
- infra：Postgres(pgvector) + Redis + MinIO Compose
