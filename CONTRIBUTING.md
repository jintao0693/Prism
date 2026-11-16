# 贡献指南

感谢你关注 Prism。本项目由 **jintao**（[@jintao0693](https://github.com/jintao0693)）维护，欢迎 Issue 与 PR。

## 开始之前

1. 阅读 [README](README.md)、[产品文档](docs/PRODUCT.md)、[技术文档](docs/TECHNICAL.md)
2. 本地能跑通「后端 8000 + 前端 3000」演示登录
3. 改动尽量小而聚焦；大功能先开 Issue 讨论

## 本地开发

### 一键（推荐）

```bash
# Windows PowerShell
.\scripts\dev.ps1

# macOS / Linux
chmod +x scripts/dev.sh && ./scripts/dev.sh
```

### 手动

见根目录 README「快速开始」。默认演示账号：`linqing@prism.demo` / `prism123`。

### 验证

```bash
# API
cd apps/api
pip install -e ".[dev]"
ruff check app
pytest -q

# Web
cd apps/web
npm run lint
npm run build
```

## 提交规范

- 分支：`feat/...`、`fix/...`、`docs/...`、`chore/...`
- Commit 说明写清「为什么」，英文或中文均可
- 不要提交 `.env`、密钥、本地数据库、`node_modules`、`.venv`
- 新增 API 请同步更新 `apps/api/README.md` 或相关 docs
- UI 改动尽量对齐 `design/prism-ui` 的视觉语言

## PR 检查清单

- [ ] 本地 lint / 测试通过
- [ ] 涉及配置时更新了 `.env.example`
- [ ] 文档与行为一致
- [ ] 无密钥或个人数据

## 行为准则

参与本仓库即表示同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 安全问题

请勿在公开 Issue 中贴密钥。报告方式见 [SECURITY.md](SECURITY.md)。
