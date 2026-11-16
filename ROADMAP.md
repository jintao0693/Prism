# Roadmap

维护者：**jintao**（[@jintao0693](https://github.com/jintao0693)）  
详细勾选进度见 [docs/PROGRESS.md](docs/PROGRESS.md)。

## Now（MVP 打磨）

- [x] 多租户登录 + 工作空间
- [x] 对话 Agent（演示模式 + 火山方舟 Chat）
- [x] Seedream 生图 / Seedance 生视频
- [x] 多模态 embedding（图搜 / 文本检索）
- [x] 设置页租户级模型配置
- [x] 开源基建（CI / 贡献文档 / 脚本）
- [x] 首跑可用性修复（CORS、密码盐、SSR API URL、mock 默认）
- [x] 测试加厚起步（security / settings + 冒烟，6 passed）
- [x] 端到端联调体验（错误提示、任务进度、空状态、会话治理）
- [ ] Docker 全栈实机验收 / 生产部署
- [ ] Alembic 正式迁移流（替代仅 create_all）
- [x] README 案例配图 / 预告成片（`docs/media/cases/`）
- [x] 产品与技术优化 backlog → [docs/OPTIMIZATION.md](docs/OPTIMIZATION.md)
- [x] 任务中心（进程内视频 Job；Worker 仍待）

## Next（Phase 2）

- [ ] 视频片段检索（切段 + 语义/视觉）
- [ ] 社媒账号绑定与定时发布（抖音 / 小红书等）
- [ ] 发布日历与失败重试
- [ ] 配额硬上限 + Worker 队列（见 OPTIMIZATION P0/T1）
- [ ] 结果快捷再创作 / Brand Pack

## Later（Phase 3）

- [ ] 巨量引擎投放草稿与素材同步
- [ ] Meta Ads 投放草稿
- [ ] 创意 ↔ 投放效果回写
- [ ] 桌面壳（Electron / Tauri）可选打包

欢迎在 Issue 里用 `roadmap` 标签提案优先级。
