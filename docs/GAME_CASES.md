# 游戏向联调案例（3 个）

> 运行时间：2026-11-16 14:06:49 · API `http://127.0.0.1:8000/api/v1`  
> 账号：`linqing@prism.demo` · 工作空间：`ws_spring`  
> 复现脚本：`scripts/run_game_cases.py`

验收多模态 Agent：知识库问答、文生图→图生图、图生视频。题材：《幻境：星落传说》。

## 案例 1：游戏设定库问答

- **目标**：知识库入库 + 勾选 KB 后的检索增强回答
- **知识库**：`kb_f5fe90b977`（文档 `ki_3a7ff86bde7c` emb=True）
- **会话**：`c_1af86d1c0c`
- **用户**：根据知识库，《幻境：星落传说》的主色是什么？立绘有什么禁忌？
- **意图 / 规划 / 工具**：`knowledge` / `kb_search_text` / `kb_search_text`
- **助手摘要**：主色深空靛 `#1B1F3B`，点缀星辉金 `#F0C75E`；立绘禁用高饱和霓虹紫，需干净轮廓与冷雾背景
- **结果**：✅ 通过

## 案例 2：游戏主视觉文生图 → 图生图改稿

- **目标**：文生图后用「再偏暖」触发图生图，并保留 `parentAssetId` 血缘
- **会话**：`c_389a95e37f`
- **步骤 A**：生成星落传说商店页头图（深空靛 + 星辉金 + 月下遗迹旅人）
- **A 意图/规划/工具**：`image` / `text_to_image` / `text_to_image`
- **A 资产 URL**：`/media/t_1/ws_spring/images/6b76939ec10c4640b645e9d484f55eaa_volc_image.png`
- **步骤 B**：再偏暖一点，保留构图与人物位置
- **B 意图/规划/工具**：`image` / `image_to_image` / `image_to_image`
- **B parentAssetId**：`asset_648d30c3b0f4`
- **B 资产 URL**：`/media/t_1/ws_spring/images/bf1d62dd0e5a40c2bf6f1b8da8fca57b_volc_image_edit.png`
- **结果**：✅ 通过

## 案例 3：主视觉 → 图生视频预告

- **目标**：承接案例 2 最近一张图，触发 `image_to_video`（含 `media.progress`）
- **会话**：`c_389a95e37f`（与案例 2 同一会话）
- **用户**：把上一张主视觉做成 5 秒预告氛围短视频：镜头缓慢推进，星尘飘落
- **意图/规划/工具**：`video` / `image_to_video` / `image_to_video`
- **parentAssetId**：`asset_63acd73d2aea`
- **资产 URL**：`/media/t_1/ws_spring/videos/6c1e44df14e64983a94c0284b047f41e_volc_i2v.mp4`
- **助手摘要**：已完成图生视频（volcengine_ark），可在资产中心查看
- **结果**：✅ 通过

## 结论

| 案例 | 能力点 | 状态 |
|------|--------|------|
| 1 | KB 入库 + 检索问答 | ✅ |
| 2 | 文生图 → 图生图血缘 | ✅ |
| 3 | 图生视频跨模态 | ✅ |

相关实现：`tool_runner.py`、`asset_memory.py`、知识库与媒体 Gateway。  
联调中修复：图生视频首帧场景不再传 `ratio`（方舟要求输出比例跟随首帧图）。

## 仍可继续优化（多模态 Agent）

1. **真·模型 tool calling**：当前是意图+规则选工具；可升级为方舟原生 function call 多步规划。
2. **对话内上传参考图**：Composer 本地上传 → 直接 i2i/i2v，不依赖「上一张生成图」。
3. **Chat 真 token 流式**：Ark `stream=true` 增量 `text.delta`（现已按帧消费 SSE，但文本仍整段返回）。
4. **Seedream/Seedance 提示词编译器**：自动注入品牌色/比例/时长/负面词。
5. **异步 Job + Worker**：超长视频任务改后台队列，HTTP 只订阅进度。
6. **资产中心上传与对话互通**：资产库选图送回会话作为参考。
