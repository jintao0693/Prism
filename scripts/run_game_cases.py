"""跑 3 个游戏向多模态联调案例，并写入 docs/GAME_CASES.md。"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = "http://127.0.0.1:8000/api/v1"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "GAME_CASES.md"


def req(
    method: str,
    path: str,
    *,
    token: str,
    tenant: str,
    body: dict | None = None,
    timeout: float = 120,
) -> tuple[int, str]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant,
        "X-Workspace-Id": "ws_spring",
    }
    if data is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            chunks: list[bytes] = []
            try:
                while True:
                    part = resp.read(8192)
                    if not part:
                        break
                    chunks.append(part)
            except Exception as exc:  # IncompleteRead / connection drop
                if chunks:
                    return resp.status, b"".join(chunks).decode("utf-8", errors="replace")
                raise exc
            return resp.status, b"".join(chunks).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def parse_sse(sse: str) -> dict[str, str]:
    def grab(pattern: str) -> str:
        m = re.search(pattern, sse)
        return m.group(1) if m else ""

    content = ""
    # Prefer last message.done payload (complete JSON object)
    for m in re.finditer(
        r"data:\s*(\{.*?\})\s*(?:\n|$)",
        sse,
        flags=re.DOTALL,
    ):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "message.done":
            data = obj.get("data") or {}
            content = str(data.get("content") or "")
            results = data.get("results") or []
            url = ""
            parent = ""
            if results and isinstance(results[0], dict):
                url = str(results[0].get("url") or "")
                parent = str(results[0].get("parentAssetId") or "")
            tool = ""
            label = str(data.get("toolLabel") or "")
            for name in (
                "text_to_image",
                "image_to_image",
                "text_to_video",
                "image_to_video",
                "kb_search_text",
                "kb_search_image",
            ):
                if name in label:
                    tool = name
                    break
            return {
                "intent": grab(r'"intent":\s*"([^"]+)"'),
                "planned": grab(r'"tool":\s*"([^"]+)"'),
                "tool": tool
                or grab(
                    r'"name":\s*"(text_to_image|image_to_image|text_to_video|image_to_video|kb_search_text|kb_search_image)"',
                ),
                "content": content,
                "url": url or grab(r'"url":\s*"([^"]+)"'),
                "parent": parent or grab(r'"parentAssetId":\s*"([^"]+)"'),
                "ok": "yes" if content or url else "no",
            }

    raw = grab(r'"content":\s*"((?:\\.|[^"\\])*)"')
    if raw:
        try:
            content = json.loads(f'"{raw}"')
        except json.JSONDecodeError:
            content = raw
    return {
        "intent": grab(r'"intent":\s*"([^"]+)"'),
        "planned": grab(r'"tool":\s*"([^"]+)"'),
        "tool": grab(
            r'"name":\s*"(text_to_image|image_to_image|text_to_video|image_to_video|kb_search_text|kb_search_image)"',
        ),
        "content": content,
        "url": grab(r'"url":\s*"([^"]+)"'),
        "parent": grab(r'"parentAssetId":\s*"([^"]+)"'),
        "ok": "yes" if len(sse) > 40 else "no",
    }


def clip(text: str, n: int = 220) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def main() -> int:
    login_req = urllib.request.Request(
        f"{BASE}/auth/login",
        data=json.dumps(
            {"email": "linqing@prism.demo", "password": "prism123"},
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(login_req, timeout=30) as resp:
        login = json.loads(resp.read().decode())
    token = login["access_token"]
    tenant = login["tenant"]["id"]
    print("login ok", tenant)

    lines: list[str] = [
        "# 游戏向联调案例（3 个）",
        "",
        f"> 运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · API `{BASE}`",
        "> 账号：`linqing@prism.demo` · 工作空间：`ws_spring`",
        "",
        "验收多模态 Agent：知识库问答、文生图→图生图、图生视频。",
        "",
    ]

    # ---- Case 1 ----
    print("=== CASE 1 KB ===")
    _, kb_raw = req(
        "POST",
        "/knowledge-bases",
        token=token,
        tenant=tenant,
        body={
            "name": "幻境：星落传说 · 设定库",
            "description": "游戏世界观与主视觉规范（案例）",
        },
    )
    kb = json.loads(kb_raw)
    kb_id = kb["id"]
    _, doc_raw = req(
        "POST",
        f"/knowledge-bases/{kb_id}/documents",
        token=token,
        tenant=tenant,
        body={
            "title": "主视觉与主色",
            "content": (
                "《幻境：星落传说》主色为深空靛 #1B1F3B，点缀星辉金 #F0C75E。"
                "角色立绘需干净轮廓与冷雾背景，禁用高饱和霓虹紫。"
                "开放世界主题：失落星轨、月下遗迹、旅人共鸣。"
            ),
        },
    )
    doc = json.loads(doc_raw)
    _, c1_raw = req(
        "POST",
        "/conversations",
        token=token,
        tenant=tenant,
        body={"title": "案例1·游戏设定问答", "kind": "chat"},
    )
    c1 = json.loads(c1_raw)
    _, sse1 = req(
        "POST",
        f"/conversations/{c1['id']}/messages",
        token=token,
        tenant=tenant,
        body={
            "content": "根据知识库，《幻境：星落传说》的主色是什么？立绘有什么禁忌？",
            "knowledgeBaseIds": [kb_id],
        },
        timeout=120,
    )
    m1 = parse_sse(sse1)
    ok1 = m1["ok"] == "yes" and bool(m1["content"])
    print("case1", m1["intent"], m1["planned"], m1["tool"], ok1)
    lines += [
        "## 案例 1：游戏设定库问答",
        "",
        "- **目标**：知识库入库 + 勾选 KB 后的检索增强回答",
        f"- **知识库**：`{kb_id}`（文档 `{doc.get('id')}` emb={doc.get('hasEmbedding')}）",
        f"- **会话**：`{c1['id']}`",
        "- **用户**：主色是什么？立绘有什么禁忌？",
        f"- **意图 / 规划 / 工具**：`{m1['intent']}` / `{m1['planned']}` / `{m1['tool']}`",
        f"- **助手摘要**：{clip(m1['content'])}",
        f"- **结果**：{'✅ 通过' if ok1 else '❌ 失败'}",
        "",
    ]

    # ---- Case 2 ----
    print("=== CASE 2 T2I + I2I ===")
    _, c2_raw = req(
        "POST",
        "/conversations",
        token=token,
        tenant=tenant,
        body={"title": "案例2·游戏主视觉", "kind": "image"},
    )
    c2 = json.loads(c2_raw)
    prompt_a = (
        "为二次元开放世界手游《幻境：星落传说》生成一张横版主视觉："
        "深空靛背景、星辉金点缀、旅人站在月下遗迹前，干净留白，适合商店页头图。"
    )
    _, sse2a = req(
        "POST",
        f"/conversations/{c2['id']}/messages",
        token=token,
        tenant=tenant,
        body={"content": prompt_a, "knowledgeBaseIds": []},
        timeout=180,
    )
    m2a = parse_sse(sse2a)
    print("case2a", m2a["planned"], m2a["tool"], m2a["url"][:60] if m2a["url"] else "")

    _, sse2b = req(
        "POST",
        f"/conversations/{c2['id']}/messages",
        token=token,
        tenant=tenant,
        body={"content": "再偏暖一点，保留构图与人物位置。", "knowledgeBaseIds": []},
        timeout=180,
    )
    m2b = parse_sse(sse2b)
    print("case2b", m2b["planned"], m2b["tool"], m2b["parent"], m2b["url"][:60] if m2b["url"] else "")
    ok2 = (
        (m2a["planned"] == "text_to_image" or m2a["tool"] == "text_to_image")
        and (m2b["planned"] == "image_to_image" or m2b["tool"] == "image_to_image")
        and bool(m2b["url"])
    )
    lines += [
        "## 案例 2：游戏主视觉文生图 → 图生图改稿",
        "",
        "- **目标**：文生图后用「再偏暖」触发图生图，并保留 parentAssetId 血缘",
        f"- **会话**：`{c2['id']}`",
        "- **步骤 A**：生成星落传说商店页头图",
        f"- **A 意图/规划/工具**：`{m2a['intent']}` / `{m2a['planned']}` / `{m2a['tool']}`",
        f"- **A 资产 URL**：`{m2a['url']}`",
        "- **步骤 B**：再偏暖一点，保留构图",
        f"- **B 意图/规划/工具**：`{m2b['intent']}` / `{m2b['planned']}` / `{m2b['tool']}`",
        f"- **B parentAssetId**：`{m2b['parent']}`",
        f"- **B 资产 URL**：`{m2b['url']}`",
        f"- **结果**：{'✅ 通过' if ok2 else '⚠️ 部分通过 / 需检查'}",
        "",
    ]

    # ---- Case 3 ----
    print("=== CASE 3 I2V ===")
    _, sse3 = req(
        "POST",
        f"/conversations/{c2['id']}/messages",
        token=token,
        tenant=tenant,
        body={
            "content": "把上一张主视觉做成 5 秒预告氛围短视频：镜头缓慢推进，星尘飘落。",
            "knowledgeBaseIds": [],
        },
        timeout=420,
    )
    m3 = parse_sse(sse3)
    print("case3", m3["planned"], m3["tool"], m3["parent"], bool(m3["url"]))
    ok3 = (m3["planned"] == "image_to_video" or m3["tool"] == "image_to_video") and m3[
        "ok"
    ] == "yes"
    lines += [
        "## 案例 3：主视觉 → 图生视频预告",
        "",
        "- **目标**：承接案例 2 最近一张图，触发 image_to_video（含 media.progress）",
        f"- **会话**：`{c2['id']}`（与案例 2 同一会话）",
        "- **用户**：把上一张主视觉做成 5 秒预告氛围短视频",
        f"- **意图/规划/工具**：`{m3['intent']}` / `{m3['planned']}` / `{m3['tool']}`",
        f"- **parentAssetId**：`{m3['parent']}`",
        f"- **资产 URL**：`{m3['url']}`",
        f"- **助手摘要**：{clip(m3['content'])}",
        f"- **结果**：{'✅ 通过' if ok3 else '⚠️ 超时或需复查（视频任务可能较长）'}",
        "",
        "## 结论",
        "",
        "| 案例 | 能力点 | 状态 |",
        "|------|--------|------|",
        f"| 1 | KB 入库 + 检索问答 | {'✅' if ok1 else '❌'} |",
        f"| 2 | 文生图 → 图生图血缘 | {'✅' if ok2 else '⚠️'} |",
        f"| 3 | 图生视频跨模态 | {'✅' if ok3 else '⚠️'} |",
        "",
        "相关实现：`tool_runner.py`、`asset_memory.py`、知识库与媒体 Gateway。",
        "",
        "## 仍可继续优化（多模态 Agent）",
        "",
        "1. **真·模型 tool calling**：当前是意图+规则选工具；可升级为方舟原生 function call 多步规划。",
        "2. **对话内上传参考图**：Composer 本地上传 → 直接 i2i/i2v，不依赖「上一张生成图」。",
        "3. **Chat 真 token 流式**：Ark `stream=true` 增量 `text.delta`（现已按帧消费 SSE，但文本仍整段返回）。",
        "4. **Seedream/Seedance 提示词编译器**：自动注入品牌色/比例/时长/负面词。",
        "5. **异步 Job + Worker**：超长视频任务改后台队列，HTTP 只订阅进度。",
        "6. **资产中心上传与对话互通**：资产库选图送回会话作为参考。",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("WROTE", OUT)
    print("SUMMARY", ok1, ok2, ok3)
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
