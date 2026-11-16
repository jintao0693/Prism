# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 风格。

## [Unreleased]

### Added

- `docs/PROGRESS.md` 开发进度单一事实来源
- 开源协作文档：CONTRIBUTING、CODE_OF_CONDUCT、SECURITY、ROADMAP
- GitHub Actions CI（API ruff/pytest、Web lint/build）
- `scripts/dev.ps1` / `scripts/dev.sh` 本地启动脚本
- API 冒烟测试（health / login）
- MIT License 与 AUTHORS（维护者 jintao）
- Docker Compose `--profile full`（api + web）与 API healthcheck
- 密码哈希随机 salt；演示账号自动修哈希
- API 测试：security / volcengine settings；`/health` 探测数据库

### Changed

- CORS 默认同时允许 `localhost:3000` 与 `127.0.0.1:3000`
- 前端 `USE_MOCK` 仅当显式 `true`；SSR 可用 `API_BASE_URL`
- 根 README 与 apps 文档细化；产品/技术文档标注作者 jintao
- `docs/STRUCTURE.md` 与仓库实际目录对齐

## [0.1.0] - 2026-11-16

### Added

- Monorepo：Next.js 前端 + FastAPI 后端
- 演示租户种子数据与登录
- 火山方舟：对话 / Seedream / Seedance / multimodal embedding
- 知识库、资产中心、设置页骨架
- infra：Postgres(pgvector) + Redis + MinIO Compose
