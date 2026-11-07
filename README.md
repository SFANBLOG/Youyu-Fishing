# 有渔渔具 · AI Agent 商城（FastAPI + LangChain + LangGraph + Vue3）

## 一句话

不是套壳 Chat：AI 助手会做意图路由、查知识库、调用商品/购物车工具、识别上传的装备图片，并把商品卡片推给用户；模型、提示词、知识库全部可以在后台页面在线改，改提示词不用动一行代码。

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | FastAPI + Tortoise ORM + **MySQL 8.0** + Pydantic v2 |
| 向量库 | **Milvus 2.x**（HNSW / COSINE，pymilvus）向量召回 + BM25 关键词召回 → RRF 名次融合 |
| 对象存储 | **MinIO**（私有桶 + `GET /api/files/{path}` 后端代理），不可用时自动降级本地磁盘 |
| AI 主链路 | **LangChain**：`ChatOpenAI` 对话/流式、`OpenAIEmbeddings` 向量、`StructuredTool` 工具协议 |
| AI 编排 | LangGraph `StateGraph` 显式节点（感知 → 意图 → 分支 → 生成 → 持久化），异常时回退顺序流水线 |
| 多模态 | OpenAI Vision 协议（图片 base64 与文本拼进同一条 `HumanMessage`） |
| 流式 | SSE `StreamingResponse`（前端 `fetch` + `ReadableStream`） |
| 鉴权 | JWT + `Depends` + 前端路由守卫（前后台双层隔离） |
| 前端 | Vue3 + Vue Router + Element Plus + Axios + Vite |
| 可视化 / 富文本 | ECharts / wangEditor 5 + markdown-it（`html:false`）+ highlight.js |
| 部署 | Docker Compose：MySQL + etcd + MinIO + Milvus + backend |

## 快速开始

### 1. 一键启动基础设施与后端（推荐）

```bash
docker compose up -d --build
```

等待健康检查全绿（Milvus 首次启动约 1-2 分钟）。Compose 已把 `DATABASE_URL`、`MILVUS_HOST`、`MINIO_ENDPOINT` 等服务名注入 backend，无需再配 `.env`。

- Swagger：`http://localhost:8000/docs`
- MinIO 控制台：`http://localhost:9001`（`minioadmin` / `minioadmin`）
- 前台测试账号：`user` / `123456`；后台管理员：`admin` / `123456`

首次启动自动建表、建 Milvus 集合、建 MinIO 桶并写入种子数据。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`；后台入口 `http://localhost:5173/admin`。

### 3. 只跑后端（基础设施由别处提供）

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate     # Windows
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

按实际情况修改 `.env` 里的 `MILVUS_HOST`、`MINIO_ENDPOINT`、`DATABASE_URL`。

### 无 Docker 时的降级模式

在 `backend/.env` 中设置：

```ini
DATABASE_URL=sqlite://db.sqlite3
VECTOR_BACKEND=off
STORAGE_BACKEND=local
LLM_FRAMEWORK=httpx
```

该模式下业务数据落 SQLite、检索退化为纯 BM25、图片存 `backend/uploads/`、LLM 走 httpx 直连，全部功能仍可离线演示。

## AI 能力怎么开

1. 后台 →「模型配置」新增 chat 模型（DeepSeek / 通义 / 智谱 / 硅基流动 / Ollama 等 OpenAI 兼容端点），填 `base_url` + `api_key` + 模型名，设为默认，点「测试连接」。
2. 再新增一条 **embedding 模型**，其输出维度必须与 `EMBED_DIM`（默认 1024）一致。维度不匹配时索引会跳过向量写入并返回 `dimension_mismatch=true`，检索层自动降级纯 BM25。
3. 后台 →「知识库管理」新增文档：切片文本写 MySQL、向量写 Milvus；可「检索测试」「重建索引」，删除文档会同步清理 Milvus 向量。
4. 后台 →「提示词配置」修改 `agent_system` / `intent` / `rag` / `tool_answer` / `chitchat` / `vision` / `recommend`，保存即时生效。
5. 前台 →「AI 选竿助手」提问，或上传装备图片。

**降级链**：LLM 不可用 → 离线兜底回复；Milvus / embedding 不可用 → 纯 BM25；MinIO 不可用 → 本地磁盘；LangGraph 不可用 → 顺序流水线。降级均在响应与对话记录中标记 `degraded`，不静默当成成功。

## 目录结构

见《项目说明文档.md》。

## 说明

- 图片存 MinIO 私有桶，前端不接触对象存储凭据，统一走 `/api/files/...` 代理读取。
- `EMBED_DIM` 变更后必须重建 Milvus 集合（换 `MILVUS_COLLECTION` 名或手动 drop），否则已写入向量维度不匹配。
- 支付为模拟状态流转（待支付 → 已支付 → 已发货 → 已完成 / 已取消），未接真实支付网关。
