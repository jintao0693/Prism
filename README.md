# Prism

多租户 SaaS 多模态 Agent：对话（文本问答 + 生图/生视频）、知识库（含图搜图）、资产中心；后续社媒发布与付费投放。

## 文档

- [产品文档](docs/PRODUCT.md)
- [技术文档](docs/TECHNICAL.md)
- [目录结构](docs/STRUCTURE.md)
- [页面 IA](docs/IA.md)
- 界面草稿：`design/prism-ui/index.html`

## 前端

```bash
cd apps/web
npm install
npm run dev
```

详见 [apps/web/README.md](apps/web/README.md)。

## 后端

```bash
cd apps/api
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

- 文档：http://localhost:8000/docs  
- 演示账号：`linqing@prism.demo` / `prism123`  
- 详见 [apps/api/README.md](apps/api/README.md)
