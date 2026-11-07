# 有渔渔具 · AI Agent 商城（FastAPI + LangGraph + Vue3）
## 一句话

不是套壳 Chat：AI 助手会做意图路由、查知识库、调用商品/购物车工具、识别上传的装备图片，并把商品卡片推给用户；模型、提示词、知识库全部可以在后台页面在线改，改提示词不用动一行代码。

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | FastAPI + Tortoise ORM（默认 SQLite，可切 MySQL）+ Pydantic |
| AI 编排 | LangGraph `StateGraph` 显式节点 + LangChain 工具协议 |
| 检索 | 300 字窗口 / 60 字重叠切片 + 向量召回 + BM25 + RRF 融合，无 embedding 时自动降级纯关键词 |
| 多模态 | OpenAI Vision 协议（图片 base64 与文本拼进同一条消息） |
| 流式 | SSE `StreamingResponse` |
| 鉴权 | JWT + `Depends` + 前端路由守卫（前后台双层隔离） |
| 前端 | Vue3 + Vue Router + Element Plus + Axios + Vite |
| 可视化 | ECharts（订单状态环形图、分类/热销条形图） |
| 富文本 | wangEditor 5 + markdown-it + highlight.js |

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

打开 `http://localhost:8000/docs` 看 Swagger。首次启动自动建表并写入种子数据。

- 前台测试账号：`user` / `123456`
- 后台管理员：`admin` / `123456`

默认 `DATABASE_URL=sqlite://db.sqlite3`，零配置可跑。要按文章用 MySQL：

```bash
docker compose up -d mysql
# .env 改为 mysql://root:youyu123@127.0.0.1:3306/youyu
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`；后台入口 `http://localhost:5173/admin`。

## AI 能力怎么开

1. 后台 →「模型配置」新增一条 OpenAI 兼容模型（DeepSeek / 通义 / 智谱 / 硅基流动 / Ollama 均可），填 `base_url` + `api_key` + 模型名，设为默认，点「测试连接」。
2. 后台 →「知识库管理」新增文档，系统自动切片，可「检索测试」「重建索引」。
3. 后台 →「提示词配置」修改 `agent_system` / `intent` / `rag` / `tool_answer` / `chitchat` / `vision` / `recommend`，保存即时生效。
4. 前台 →「AI 选竿助手」提问，或上传装备图片。

**没配模型也不会崩**：LLM 不可用、向量库缺失时自动降级为离线兜底回复，并把工具结果 / 检索命中原文直接呈现给用户。

## 目录结构

见《项目说明文档.md》。

## 说明

- 图片、富文本、商品规格等以 JSON 字段存储，避免为示例项目引入对象存储依赖。
- 向量以 JSON 数组存 SQLite，用 numpy 做余弦；生产可替换为 Milvus / pgvector，检索接口已抽象。
- 支付为模拟状态流转（待支付 → 已支付 → 已发货 → 已完成 / 已取消），未接真实支付网关。
