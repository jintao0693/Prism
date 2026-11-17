# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 风格。

## [Unreleased]

### Added

- Seedance 2.x 多模态参考生视频：`reference_image_urls` / 首尾帧互斥、最长约 15s；`reference_to_video` Provider API
- README 明星案例：分镜板 + 约 15s 成片，并用 `<video>` 在 GitHub 内嵌可播放（`case-adv-15s.mp4`）
- README / GAME_CASES 高级案例：母版血缘树、定妆多镜叙事板（`docs/media/cases/case-adv-*`）
- 前端体验打磨：会话切换防闪烁与加载重试、Enter 发送、结果快捷再创作、KB 命名创建、设置/资产失败可恢复、ConfirmDialog / Markdown 气泡

- 多模态 Agent 统一 `tool_runner`：文/图生图、文/图生视频、KB 检索；资产记忆与 `parentAssetId` 血缘
- 对话多轮上下文：滑动窗 + 摘要检查点；usage 触发自动压缩；手动 `POST .../compact`
- 多模态知识库：图片入库/检索/以图搜图、补齐向量、批量上传；Postgres pgvector / SQLite JSON 双路径
- SSE 真流式 + 视频 `media.progress`；图生视频失败时回传可读错误事件
- 游戏向产品案例：`scripts/run_game_cases.py` + `docs/GAME_CASES.md`；根 README 改为产品叙事并内嵌发行周三案例
- 对话附参考图：`POST /assets/upload` + `referenceAssetIds` → 图生图 / 图生视频
- 创作对话前端真流式气泡（SSE 增量文本 / 工具进度 / 中途结果卡）
- 对话与资产中心错误态、空状态引导；资产中心支持上传图片
- 素材预览修复：入库旁路 JPEG 缩略图、`thumbUrl` / `previewKind`；视频海报不再误用 `<video>`；媒体 URL 始终用浏览器可达 origin
- 本月用量按生成资产实算（侧栏 / 设置同步）；生图生视频后即时记账
- 资产中心「送回对话」：新建会话并挂上参考图，可直接图生图 / 图生视频
- README / GAME_CASES 嵌入发行周真实出图与预告成片（`docs/media/cases/`）
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
