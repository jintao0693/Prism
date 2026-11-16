"""跑《幻境：星落传说》发行周 3 个产品案例，并写入 docs/GAME_CASES.md。"""

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

KB_DOC = """
《幻境：星落传说》发行视觉规范（摘要）

品牌主色：深空靛 #1B1F3B；点缀色：星辉金 #F0C75E。
角色立绘：干净轮廓、冷雾背景；禁用高饱和霓虹紫；避免赛博霓虹边框。
世界观关键词：失落星轨、月下遗迹、旅人共鸣、开放世界探索。
商店页头图：横版、主体偏左或居中留白、适合应用商店截图区；气质安静、有召唤感。
社媒预告：5 秒内讲清氛围即可，镜头宜缓，忌剧烈甩镜与过曝金光。
禁止：与竞品「霓虹地下城」撞色；禁止把主色改成纯黑或玫红。
""".strip()


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
    for m in re.finditer(r"data:\s*(\{.*?\})\s*(?:\n|$)", sse, flags=re.DOTALL):
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


def clip(text: str, n: int = 280) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def mark(ok: bool) -> str:
    return "✅" if ok else "❌"


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
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---- Case 1 ----
    print("=== CASE 1 KB ===")
    _, kb_raw = req(
        "POST",
        "/knowledge-bases",
        token=token,
        tenant=tenant,
        body={
            "name": "幻境：星落传说 · 设定库",
            "description": "发行周视觉规范与商店页 / 预告约束",
        },
    )
    kb = json.loads(kb_raw)
    kb_id = kb["id"]
    _, doc_raw = req(
        "POST",
        f"/knowledge-bases/{kb_id}/documents",
        token=token,
        tenant=tenant,
        body={"title": "发行视觉规范（摘要）", "content": KB_DOC},
    )
    doc = json.loads(doc_raw)
    _, c1_raw = req(
        "POST",
        "/conversations",
        token=token,
        tenant=tenant,
        body={"title": "发行周·规范对齐 brief", "kind": "chat"},
    )
    c1 = json.loads(c1_raw)
    q1 = (
        "我们要开商店页和预告片。根据知识库，请用 brief 口吻回答："
        "1) 主色与点缀色；2) 立绘与配色禁忌；3) 商店页头图气质要求；"
        "4) 做什么会和竞品撞车。尽量条理清晰，方便直接交给美术。"
    )
    _, sse1 = req(
        "POST",
        f"/conversations/{c1['id']}/messages",
        token=token,
        tenant=tenant,
        body={"content": q1, "knowledgeBaseIds": [kb_id]},
        timeout=120,
    )
    m1 = parse_sse(sse1)
    ok1 = m1["ok"] == "yes" and bool(m1["content"])
    print("case1", m1["intent"], m1["planned"], m1["tool"], ok1)

    # ---- Case 2 ----
    print("=== CASE 2 T2I + I2I ===")
    _, c2_raw = req(
        "POST",
        "/conversations",
        token=token,
        tenant=tenant,
        body={"title": "发行周·商店页 KV 改稿", "kind": "image"},
    )
    c2 = json.loads(c2_raw)
    prompt_a = (
        "为二次元开放世界手游《幻境：星落传说》生成一张应用商店横版头图："
        "深空靛 #1B1F3B 背景，星辉金 #F0C75E 点缀，旅人站在月下遗迹前，"
        "干净留白、安静召唤感，适合商店页首屏，不要霓虹紫，不要文字水印。"
    )
    _, sse2a = req(
        "POST",
        f"/conversations/{c2['id']}/messages",
        token=token,
        tenant=tenant,
        body={"content": prompt_a, "knowledgeBaseIds": [kb_id]},
        timeout=180,
    )
    m2a = parse_sse(sse2a)
    print("case2a", m2a["planned"], m2a["tool"], (m2a["url"] or "")[:60])

    prompt_b = (
        "发行觉得偏冷、召回不够。请再偏暖一点，保留构图与人物位置，"
        "星辉金可以更明显一点，仍禁止霓虹紫。"
    )
    _, sse2b = req(
        "POST",
        f"/conversations/{c2['id']}/messages",
        token=token,
        tenant=tenant,
        body={"content": prompt_b, "knowledgeBaseIds": [kb_id]},
        timeout=180,
    )
    m2b = parse_sse(sse2b)
    print(
        "case2b",
        m2b["planned"],
        m2b["tool"],
        m2b["parent"],
        (m2b["url"] or "")[:60],
    )
    ok2 = (
        (m2a["planned"] == "text_to_image" or m2a["tool"] == "text_to_image")
        and (m2b["planned"] == "image_to_image" or m2b["tool"] == "image_to_image")
        and bool(m2b["url"])
    )

    # ---- Case 3 ----
    print("=== CASE 3 I2V ===")
    prompt_c = (
        "KV 已定。请把上一张主视觉做成 5 秒商店详情 / 社媒首发氛围预告："
        "镜头缓慢推进，星尘轻轻飘落，气质与静帧一致，不要剧烈甩镜、不要过曝金光。"
    )
    _, sse3 = req(
        "POST",
        f"/conversations/{c2['id']}/messages",
        token=token,
        tenant=tenant,
        body={"content": prompt_c, "knowledgeBaseIds": [kb_id]},
        timeout=420,
    )
    m3 = parse_sse(sse3)
    print("case3", m3["planned"], m3["tool"], m3["parent"], bool(m3["url"]))
    ok3 = (m3["planned"] == "image_to_video" or m3["tool"] == "image_to_video") and (
        m3["ok"] == "yes"
    )

    lines = [
        "# 游戏向产品案例：《幻境：星落传说》发行周",
        "",
        f"> 最近联调：{run_at} · API `{BASE}`  ",
        "> 账号 `linqing@prism.demo` · 工作空间 `ws_spring`  ",
        "> 复现：`python scripts/run_game_cases.py`  ",
        "> 产品叙事摘要已写入根 [README.md](../README.md)",
        "",
        "三个案例不是孤立的接口冒烟，而是同一发行周里的连续作业："
        "**对齐规范 → 商店页 KV 改稿 → 静帧拉预告**。",
        "",
        "---",
        "",
        "## 案例 1 · 发行周：把「能拍的规范」问清楚",
        "",
        "### 业务背景",
        "",
        "商店页、社媒 KV、预告片同一周开工。视觉规范必须先对齐，否则后面三组素材会各说各话。",
        "",
        "### 用户动作",
        "",
        "1. 创建知识库「幻境：星落传说 · 设定库」",
        "2. 入库发行视觉规范（主色 / 禁忌 / 商店页气质 / 竞品撞车风险）",
        "3. 创作对话勾选该库，要一份可直接交给美术的 brief",
        "",
        "### 产品验收",
        "",
        "| 项 | 结果 |",
        "|----|------|",
        f"| 知识库创建 + 文档入库 | {mark(bool(kb_id and doc.get('id')))} `{kb_id}` / `{doc.get('id')}` emb={doc.get('hasEmbedding')} |",
        f"| 勾选 KB 后检索增强问答 | {mark(ok1)} `{m1['intent']}` → `{m1['tool'] or m1['planned']}` |",
        f"| 会话 | `{c1['id']}` |",
        f"| 助手摘要 | {clip(m1['content'])} |",
        "",
        "---",
        "",
        "## 案例 2 · 商店页主视觉：从一句话到可改稿的 KV",
        "",
        "### 业务背景",
        "",
        "商店页头图要横版、深空靛底、星辉金点缀、月下遗迹旅人。初稿偏冷，发行要求构图与人物不动，整体再偏暖。",
        "",
        "### 用户动作",
        "",
        "1. 同一会话下达完整商店页 brief → 文生图",
        "2. 「再偏暖 / 构图不动」→ 图生图",
        "3. 资产中心对照两版改稿血缘",
        "",
        "### 产品验收",
        "",
        "| 项 | 结果 |",
        "|----|------|",
        f"| 会话 | `{c2['id']}` |",
        f"| 首轮文生图 | {mark(m2a['planned'] == 'text_to_image' or m2a['tool'] == 'text_to_image')} `{m2a['url']}` |",
        f"| 「再偏暖」图生图 | {mark(m2b['planned'] == 'image_to_image' or m2b['tool'] == 'image_to_image')} `{m2b['url']}` |",
        f"| 改稿 parentAssetId | {mark(bool(m2b['parent']))} `{m2b['parent']}` |",
        f"| 案例整体 | {mark(ok2)} |",
        "",
        "---",
        "",
        "## 案例 3 · 预告氛围片：定稿静帧拉成 5 秒片",
        "",
        "### 业务背景",
        "",
        "KV 已定。还要 5 秒氛围预告给商店详情与社媒首发：缓慢推进 + 星尘飘落，气质跟主视觉一致。",
        "",
        "### 用户动作",
        "",
        "1. 仍在案例 2 同一会话",
        "2. 要求把上一张主视觉做成 5 秒氛围预告",
        "3. 成片与静帧一并进资产中心",
        "",
        "### 产品验收",
        "",
        "| 项 | 结果 |",
        "|----|------|",
        f"| 识别为图生视频 | {mark(m3['planned'] == 'image_to_video' or m3['tool'] == 'image_to_video')} `{m3['tool'] or m3['planned']}` |",
        f"| 引用上一张图 | {mark(bool(m3['parent']))} parent=`{m3['parent']}` |",
        f"| 成片 URL | `{m3['url']}` |",
        f"| 助手摘要 | {clip(m3['content'])} |",
        f"| 案例整体 | {mark(ok3)} |",
        "",
        "---",
        "",
        "## 闭环一览",
        "",
        "| 案例 | 业务问题 | 产品能力 | 状态 |",
        "|------|----------|----------|------|",
        f"| 1 | 规范散、怕说错 | 知识库约束对话 brief | {mark(ok1)} |",
        f"| 2 | 商店页要快迭代 | 文生图 → 图生图血缘改稿 | {mark(ok2)} |",
        f"| 3 | 静帧要变成预告 | 图生视频跨模态接力 | {mark(ok3)} |",
        "",
        "```text",
        "规范入库 → 对话对齐 brief",
        "        → 商店页 KV 文生图",
        "        → 「再偏暖」图生图改稿",
        "        → 定稿静帧 → 5 秒氛围预告",
        "        → 全部进入资产中心",
        "```",
        "",
        "## 仍可继续优化（产品侧）",
        "",
        "1. 对话里直接上传参考图做改稿 / 预告",
        "2. 从知识库自动编译品牌色、禁忌词进提示词",
        "3. 资产中心选历史 KV 送回会话继续改",
        "4. 长视频改异步任务，对话只订进度",
        "5. 多步原生 tool calling（一次说清：出图 + 出预告）",
        "6. Chat 真流式字词输出",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("WROTE", OUT)
    print("SUMMARY", ok1, ok2, ok3)
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
