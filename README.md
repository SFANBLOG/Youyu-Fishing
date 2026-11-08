# 🎣 有渔渔具

**AI Agent 渔具商城** — 不是套壳 Chat：会做意图路由、查知识库、调用商品/购物车工具、识别上传的装备图片，并把商品卡片推给用户；模型、提示词、知识库全部可在后台在线改，改提示词不用动一行代码。

---

## 目录

- [一、项目背景](#一项目背景)
- [二、功能特性](#二功能特性)
- [三、运行效果与演示入口](#三运行效果与演示入口)
- [四、技术栈](#四技术栈)
- [五、系统架构](#五系统架构)
- [六、Agent 工作流与在线配置](#六agent-工作流与在线配置)
- [七、快速开始（Docker / 本地）](#七快速开始docker--本地)
- [八、测试、工程要点与边界](#八测试工程要点与边界)
- [九、环境变量](#九环境变量)
- [十、API 一览](#十api-一览)
- [十一、项目结构](#十一项目结构)
- [十二、参与贡献](#十二参与贡献)
- [十三、免责声明与许可证](#十三免责声明与许可证)

---

## 一、项目背景

> *"想买根竿，问了半天客服也分不清溪流竿和路亚竿；问 AI 只会回一段通用科普，想加购物车还得自己再搜一遍。"*

传统电商的搜索框只认关键词，通用 ChatBot 又只回答问题、不碰业务。对渔具这类**强参数、强场景**的商品，用户真正需要的是「说得清需求 → 找得对装备 → 能直接下单」的一条链路。

| 痛点 | 现状 |
| :--- | :--- |
| 🎯 **选竿靠猜** | 调性、长度、饵重、作钓场景参数分散，关键词搜索很难一次命中 |
| 💬 **AI 只会聊** | 常见套壳 Chat 不查知识库、不调商品工具，回答与商城数据脱节 |
| 🔧 **改不动** | 模型、提示词、知识库写死在代码里，运营改一句话就要重新发版 |

**有渔渔具** 把 AI 助手接进真实商城业务：LangGraph 显式编排「感知 → 意图 → 分支 → 生成 → 持久化」，五个意图分支分别走知识库检索、商品工具、相似推荐、图片理解与闲聊；后台可在线维护模型配置、7 类提示词与知识库文档，前台直接拿到带引用的回答和商品卡片。

> 💡 *让 AI 不只是回答问题，而是把生意跑完一轮。*

---

## 二、功能特性

| 能力 | 说明 |
|---|---|
| **五路意图路由** | `rag` / `tool` / `recommend` / `vision` / `chitchat` 显式分支，LLM 失败时降级为关键词规则，不把不确定性丢给用户 |
| **混合检索 RAG** | 文档按 **300 字窗口 + 60 字重叠**切片（优先句末断开）；Milvus HNSW/COSINE 向量召回 + BM25 关键词召回 → **RRF 名次融合**（向量 0.6 / 关键词 0.4），切片文本存 MySQL、向量写 Milvus，主键一致可回链原文 |
| **多模态选竿** | 图片 base64 与文本拼进同一条 `HumanMessage`，走 OpenAI Vision 协议识别装备，再与商品库匹配 |
| **商品工具调用** | LangChain `StructuredTool` 暴露商品搜索、加入购物车、相似推荐、订单查询等工具，模型输出可直接作用于业务数据 |
| **商品卡片推送** | 前台展示回答正文 + 结构化商品卡片，后台记录引用、推荐结果、命中节点与工具调用，全链路可解释 |
| **AI 能力在线配置** | 后台管理对话 / 向量 / 图片模型（任意 OpenAI 兼容端点）、7 类提示词与知识库文档，测试连接、检索测试、重建索引均在页面完成，保存即时生效 |
| **SSE 流式输出** | `StreamingResponse` 推送 `meta` / `delta` / `done` / `error` 事件；前端流式期间只做纯文本拼接、`done` 后一次性语法高亮，避免代码块未闭合反复解析 |
| **完整商城闭环** | 分类 / 商品 / 收藏 / 购物车 / 结算 / 订单流转 / 评价 / 资讯 / 轮播 / 公告，配套后台会员、订单、评价与 ECharts 数据看板 |
| **私有桶与双层鉴权** | 图片存 MinIO **私有桶**，统一由 `GET /api/files/{path}` 后端代理读取，前端不接触对象存储凭据；JWT + `Depends` 区分 user / admin，前端路由守卫 + Axios 401 拦截 |
| **全链路降级** | LLM 不可用 → 离线兜底回复；Milvus / embedding 不可用 → 纯 BM25；MinIO 不可用 → 本地磁盘；LangGraph 不可用 → 顺序流水线。降级均在响应与对话记录中标记 `degraded`，不静默当成成功 |

---

## 三、运行效果与演示入口

| 入口 | 地址 | 说明 |
|:---|:---|:---|
| 前台商城 | [http://localhost:5173](http://localhost:5173) | 首页 / 商品 / AI 选竿助手 / 购物车 / 订单 |
| 后台管理 | [http://localhost:5173/admin](http://localhost:5173/admin) | 数据看板 / 模型配置 / 提示词配置 / 知识库 / 对话记录 |
| API 文档（Swagger） | [http://localhost:8000/docs](http://localhost:8000/docs) | 全量 REST 接口 |
| MinIO 控制台 | [http://localhost:9001](http://localhost:9001) | `minioadmin` / `minioadmin` |

| 角色 | 账号 | 密码 |
|:---|:---|:---|
| 前台测试用户 | `user` | `123456` |
| 后台管理员 | `admin` | `123456` |

首次启动自动写入种子数据：**2 个账号、6 个渔具分类、12 个商品、3 条资讯、3 张轮播、2 条公告、7 条默认提示词、2 篇知识库文档**。

> 仓库暂未收录界面截图；内置的演示占位素材（商品图 / 轮播图 SVG）位于 `backend/static/demo/`，可直接启动后查看实际页面。

---

## 四、技术栈

**Web 端（Vue 3）**

| 技术 | 说明 |
|:---|:---|
| Vue 3 + TypeScript | 组件化、类型安全的现代化前端 |
| Vue Router | 前后台路由 + 登录守卫 |
| Element Plus | UI 组件库 |
| Axios | REST 请求拦截器 + token，对话走 `fetch` + `ReadableStream` 消费 SSE |
| ECharts / wangEditor 5 | 数据看板可视化 / 后台富文本编辑 |
| markdown-it + highlight.js | `html:false` 渲染回答，关闭原始 HTML 防 XSS |
| Vite | 开发服务器与构建 |

**服务端（Python FastAPI）**

| 技术 | 说明 |
|:---|:---|
| FastAPI + Pydantic v2 | 异步接口 + 自动 Swagger 文档，统一 `Result` 响应与全局异常处理 |
| Tortoise ORM + aiomysql | MySQL 8.0 业务数据，`generate_schemas(safe=True)` 自动建表、带退避重连 |
| PyJWT | JWT 签发 / 解析 + `Depends` 用户与管理员双层依赖 |
| LangChain | `ChatOpenAI` 对话 / 流式、`OpenAIEmbeddings` 向量、`StructuredTool` 工具协议 |
| LangGraph | `StateGraph` 显式节点编排，异常时回退顺序流水线 |
| httpx | LangChain 未安装或异常时的直连兜底，超时 / 401 / 额度不足统一降级离线回复 |
| OpenAI Vision 协议 | 图片 base64 与文本拼进同一条 `HumanMessage` 做装备识别 |

**检索与存储**

| 技术 | 说明 |
|:---|:---|
| Milvus 2.x（pymilvus） | HNSW / COSINE 向量索引，按 `doc_id` 增删查，兼容 2.3 / 2.4 建集合 API |
| BM25 + RRF | 关键词召回与向量召回经 `1/(60+rank)` 名次融合，规避两套分数量纲差异 |
| MinIO | 私有桶对象存储，不可用时自动降级本地 `uploads/` 目录 |
| MySQL / SQLite | 业务数据主库 / 无 Docker 时的降级库 |

**部署**

| 技术 | 说明 |
|:---|:---|
| Docker Compose | MySQL + etcd + MinIO + Milvus + backend 五服务一键编排，健康检查按序启动 |
| Vite dev server | 前端本地开发服务器（`5173`），后端 `8000`；未包含生产静态托管配置，部署时按需接入 |

---

## 五、系统架构

系统采用**前后端分离 + 显式 Agent 编排**架构：前端只负责展示与流式消费，服务端把「感知、意图、检索、工具、生成、落库」拆成可观测节点，外部依赖全部有降级路径。

```mermaid
flowchart TB
    subgraph L1["① 客户端层"]
        direction LR
        W["Vue 3 前台商城<br/>商品 · 购物车 · AI 选竿助手"]
        A["Vue 3 后台管理<br/>看板 · 模型 · 提示词 · 知识库"]
    end

    subgraph L2["② API 网关层 · FastAPI"]
        direction LR
        A1["认证鉴权<br/>JWT + Depends · 路由守卫"]
        A2["统一响应<br/>Result · 全局异常 · CORS"]
        A3["路由<br/>REST + SSE · /api 前缀"]
    end

    subgraph L3["③ Agent 编排层 · LangGraph StateGraph"]
        direction LR
        N1["perceive<br/>文本 + 图片感知"]
        N2["intent<br/>五路意图路由"]
        N3["branch<br/>RAG / Tool / Recommend / Vision / Chitchat"]
        N4["generate<br/>ChatOpenAI SSE 流式"]
        N5["persist<br/>消息 · 轨迹 · 引用 · 推荐结果"]
        N1 --> N2 --> N3 --> N4 --> N5
    end

    subgraph L4["④ 检索与工具链路"]
        direction LR
        E1["切片 300 / 重叠 60<br/>句末优先断开"]
        V1["Milvus 向量召回<br/>HNSW · COSINE"]
        B1["BM25 关键词召回"]
        F1["RRF 融合<br/>1 / (60 + rank)"]
        T1["StructuredTool<br/>商品搜索 · 加购 · 订单查询"]
        E1 --> V1 --> F1
        B1 --> F1
    end

    subgraph L5["⑤ 存储与基础设施"]
        direction LR
        S1["MySQL 8<br/>Tortoise ORM · 切片文本"]
        S2["Milvus<br/>向量主键 = 切片 id"]
        S3["MinIO 私有桶<br/>/api/files 代理读取"]
        S4["模型 / 提示词配置<br/>后台在线维护"]
    end

    L1 --> L2 --> L3
    N3 --> L4
    F1 --> N4
    T1 --> N4
    L3 --> L5
    L4 --> L5
```

### 5.1 一次 AI 对话的完整链路

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户 / 前端
    participant API as FastAPI /api
    participant G as LangGraph StateGraph
    participant R as 混合检索 RAG
    participant T as 商品工具 / LLM
    participant D as MySQL · Milvus · MinIO

    U->>API: POST /api/chat/stream（文本 + 图片）
    API->>G: 初始化 AgentState
    API-->>U: SSE meta（session_id）

    G->>T: perceive 图片交 Vision 识别装备
    T-->>G: 装备描述 + 用户文本
    G->>T: intent 意图分类（失败降级关键词规则）
    T-->>G: rag / tool / recommend / vision / chitchat

    alt 知识库问答
        G->>R: Milvus 向量 + BM25 → RRF 融合
        R-->>G: Top-K 切片 + 引用
    else 商品 / 交易诉求
        G->>T: StructuredTool 搜索商品 / 加购 / 查订单
        T-->>G: 结构化结果 + 商品卡片
    else 图片选竿
        G->>T: 视觉结果与商品库匹配
        T-->>G: 推荐商品卡片
    end

    G->>T: generate 组装上下文，ChatOpenAI 流式生成
    T-->>U: SSE delta 逐块推送
    G->>D: persist 消息、意图、工具、引用、执行轨迹
    API-->>U: SSE done（含 degraded 标记）
```

### 5.2 混合检索与降级链

**检索链路**：知识库文档 → 300 字窗口 + 60 字重叠切片（块携带 `doc_id / idx / start / end`）→ 切片文本写 MySQL、`LangChain Embeddings` 向量写 Milvus → 查询时向量通道与 BM25 通道各召回 → **RRF 名次融合**（向量权重 0.6 / 关键词 0.4）→ 注入上下文并附引用。Milvus 或 embedding 不可用时降级纯 BM25 并标记 `degraded=true`。

**降级矩阵**

| 场景 | 表现 | 标记 |
|:---|:---|:---|
| LLM 未配置 / 超时 / 401 / 额度不足 | httpx 直连兜底，仍失败则离线兜底回复 | `degraded` |
| Milvus / embedding 不可用 | 检索退化为纯 BM25 | `degraded` + `dimension_mismatch` |
| MinIO 连接失败 | 本次进程内切本地 `uploads/`，上传响应仍是 wangEditor 协议 | 前端无感 |
| LangGraph 不可用 | 回退顺序流水线 | `degraded` |
| MySQL 不可用（本地模式） | 切 `sqlite://db.sqlite3` | 配置显式指定 |

> 关键原则：**降级不静默**。响应体与后台「对话记录」都会留下 `degraded`、命中节点、工具与引用，方便复盘本次回答到底走了哪条链路。

---

## 六、Agent 工作流与在线配置

### 6.1 LangGraph 显式节点

```
StateGraph(AgentState)
 │   START
 ▼
 ├─ 👁 perceive    — 解析文本 + 图片（Vision 识别装备）
 ▼
 ├─ 🧭 intent      — 意图路由 rag / tool / recommend / vision / chitchat
 │                    （LLM 失败降级关键词规则）
 ▼
 ├─ 🔀 branch      — rag      知识库混合检索（Milvus + BM25 + RRF），注入引用
 │                    tool     StructuredTool 商品搜索 / 加购 / 订单查询
 │                    recommend 相似商品 / 热销推荐，产出商品卡片
 │                    vision   图片理解结果 + 商品匹配
 │                    chitchat 闲聊
 ▼
 ├─ ✍ generate     — 组装上下文，ChatOpenAI SSE 流式输出（无模型 → 离线兜底）
 ▼
 └─ 💾 persist     — 落库消息、意图/工具/引擎标签、执行轨迹、引用、推荐结果
 ▼
 END
```

| 阶段 | 输入 | 输出 |
|:---|:---|:---|
| `perceive` | 用户文本、上传图片 | 规范化文本 + 装备识别结果 |
| `intent` | 上下文 + 意图提示词 | 五类意图之一 |
| `branch` | 意图 + 会话状态 | 检索片段 / 工具结果 / 商品卡片 / 闲聊上下文 |
| `generate` | 组装后的上下文 | SSE 流式回答 |
| `persist` | 全流程状态 | 消息、执行轨迹、引用、`degraded` 标记 |

工作流实现在 `backend/app/agent/graph.py`（StateGraph 编排 + 顺序流水线兜底），节点动作位于 `nodes.py`，工具定义位于 `tools.py`。

### 6.2 StructuredTool 工具集

| 工具 | 作用 | 典型触发 |
|:---|:---|:---|
| 商品搜索 | 按关键词 / 分类 / 参数检索在售商品 | 「推荐一根 2.1 米的溪流竿」 |
| 相似推荐 | 基于当前商品返回相似 / 热销商品 | 商品详情页、推荐意图 |
| 加入购物车 | 把指定 SKU 写入当前用户购物车 | 「把这个加到购物车」 |
| 订单查询 | 查询当前用户订单与状态 | 「我上周的订单到哪了」 |

### 6.3 后台在线可改什么

| 配置 | 位置 | 说明 |
|:---|:---|:---|
| 模型配置 | 后台 →「模型配置」 | chat / embedding / vision 模型，填 `base_url` + `api_key` + 模型名，可设默认、启停、测试连接；兼容 DeepSeek / 通义 / 智谱 / 硅基流动 / Ollama 等 OpenAI 兼容端点 |
| 提示词配置 | 后台 →「提示词配置」 | `agent_system` / `intent` / `rag` / `tool_answer` / `chitchat` / `vision` / `recommend` 共 7 类，支持变量渲染预览，保存即时生效 |
| 知识库 | 后台 →「知识库管理」 | 文档 CRUD、自动切片并写 Milvus、切片预览（含 `has_vector`）、检索测试、重建索引；删除文档同步清理向量 |

> ⚠️ embedding 模型输出维度必须与 `EMBED_DIM`（默认 1024）一致。维度不匹配时索引跳过向量写入并返回 `dimension_mismatch=true`，检索层自动降级纯 BM25；变更维度后必须换 `MILVUS_COLLECTION` 名或手动 drop 重建集合。

### 6.4 SSE 事件协议

| 事件 | 载荷 | 说明 |
|:---|:---|:---|
| `meta` | `{session_id}` | 会话建立 |
| `delta` | `{text}` | 逐块回答文本 |
| `done` | `{answer, intent, tool, engine, degraded, trace, sources, recommendations}` | 生成结束，回传意图 / 工具 / 引擎标签、执行轨迹、引用与推荐商品卡片 |
| `error` | `{message}` | Agent 执行失败 |

---

## 七、快速开始（Docker / 本地）

### 前置要求

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js](https://nodejs.org/) 18+（Web 端开发）
- [Python](https://www.python.org/) 3.10+（服务端本地开发，可选）

### 7.1 方式一：Docker Compose 一键部署（推荐）

```bash
# 1. 构建并后台启动（首次拉取镜像较慢，Milvus 健康检查约 1-2 分钟）
docker compose up -d --build

# 2. 查看状态与日志
docker compose ps
docker compose logs -f backend
```

Compose 已把 `DATABASE_URL`、`MILVUS_HOST`、`MINIO_ENDPOINT` 等服务名注入 backend，**无需再配 `.env`**。首次启动自动建表、建 Milvus 集合、建 MinIO 桶并写入种子数据。

**服务清单（5 个容器）**

| 服务 | 镜像 | 端口（宿主机 → 容器） | 用途 |
|:---|:---|:---|:---|
| `mysql` | mysql:8.0 | 3306 → 3306 | 业务数据库 |
| `etcd` | quay.io/coreos/etcd:v3.5.5 | — | Milvus 元数据 |
| `minio` | minio/minio | 9000 / 9001 | 对象存储（Milvus 与后端共用） |
| `milvus` | milvusdb/milvus:v2.4.0 | 19530 / 9091 | 向量数据库 |
| `backend` | 本地构建 | 8000 → 8000 | FastAPI AI 服务端 |

**访问地址**

| 入口 | 地址 |
|:---|:---|
| 前台商城 | [http://localhost:5173](http://localhost:5173) |
| 后台管理 | [http://localhost:5173/admin](http://localhost:5173/admin) |
| API 文档 | [http://localhost:8000/docs](http://localhost:8000/docs) |
| MinIO 控制台 | [http://localhost:9001](http://localhost:9001) |

### 7.2 方式二：前端本地开发

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`；后台入口 `http://localhost:5173/admin`。

### 7.3 方式三：只跑后端（基础设施由别处提供）

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate     # Windows
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

按实际情况修改 `.env` 里的 `MILVUS_HOST`、`MINIO_ENDPOINT`、`DATABASE_URL`。

### 7.4 无 Docker 时的降级模式

在 `backend/.env` 中设置：

```ini
DATABASE_URL=sqlite://db.sqlite3
VECTOR_BACKEND=off
STORAGE_BACKEND=local
LLM_FRAMEWORK=httpx
```

该模式下业务数据落 SQLite、检索退化为纯 BM25、图片存 `backend/uploads/`、LLM 走 httpx 直连，**全部功能仍可离线演示**。

### 7.5 开启 AI 能力

1. 后台 →「模型配置」新增 chat 模型，填 `base_url` + `api_key` + 模型名，设为默认，点「测试连接」。
2. 再新增一条 embedding 模型，输出维度与 `EMBED_DIM`（默认 1024）一致。
3. 后台 →「知识库管理」新增文档，可「检索测试」「重建索引」，删除文档同步清理 Milvus 向量。
4. 后台 →「提示词配置」调整 7 类提示词，保存即时生效。
5. 前台 →「AI 选竿助手」提问，或上传装备图片。

---

## 八、测试、工程要点与边界

### 8.1 自动化测试

```bash
cd backend
python -m pytest
```

| 用例文件 | 覆盖 |
|:---|:---|
| `tests/test_chunker.py` | 300/60 切片窗口、句末优先断开、块元数据回链 |
| `tests/test_retriever.py` | BM25 / 向量双路召回、RRF 名次融合、降级纯 BM25 |
| `tests/test_infra.py` | Milvus / MinIO 初始化失败时的基础设施降级行为 |

### 8.2 关键工程点

| # | 要点 | 做法 |
|:---|:---|:---|
| 1 | 混合检索量纲不一 | RRF 用名次融合（向量 0.6 / 关键词 0.4），不直接相加两套分数 |
| 2 | 多厂商模型兼容 | 全走 OpenAI 兼容协议；LangChain 主链路 + httpx 兜底，异常统一降级离线回复 |
| 3 | 流式渲染抖动 | 流式期间纯文本拼接、跳过语法高亮，`done` 后一次性高亮 |
| 4 | XSS | markdown-it 配置 `html:false`，用户内容中的原始 HTML 不渲染 |
| 5 | 双层鉴权 | 后端 `Depends` 区分 user / admin + 前端路由守卫 + Axios 401 拦截 |
| 6 | 统一响应 | `Result.success / Result.fail` + 全局异常处理器，分页统一 `{items,total,page,size}` |
| 7 | Pydantic / ORM 边界 | 登录态 `Account` 是 Pydantic 对象，取 `id` 再查 ORM，不直接传给 `get_or_none` |
| 8 | 私有桶代理 | MinIO 不设公开读，上传返回 `/api/files/{object_name}`，后端校验路径与扩展名后代理输出 |

### 8.3 边界与 TODO

- 支付为状态机模拟（待支付 → 已支付 → 已发货 → 已完成 / 已取消），**未接真实支付网关**；短信 / 邮件未接。
- MySQL 由 Tortoise `generate_schemas(safe=True)` 自动建表，**未接 Alembic / aerich 迁移**，生产应补迁移工具。
- 未做分布式会话、限流、审计日志与压测，属生产化补强项。
- `EMBED_DIM` 变更维度后必须重建 Milvus 集合，否则已写入向量维度不匹配。
- 清空演示数据：删除 MySQL 的 `youyu` 库（或 `docker compose down -v` 后重建），并删除 / 重建 Milvus 集合与 MinIO 桶。

---

## 九、环境变量

> 完整模板见 `backend/.env.example`；Docker Compose 部署时同名变量已由 `docker-compose.yml` 注入。

| 分组 | 变量 | 默认值 | 说明 |
|:---|:---|:---|:---|
| 应用 | `APP_NAME` | `有渔渔具 AI Agent` | 应用名 |
| 数据库 | `DATABASE_URL` | `mysql://root:youyu123@127.0.0.1:3306/youyu` | MySQL 连接串；无 Docker 时可改 `sqlite://db.sqlite3` |
| | `DB_RETRY` / `DB_RETRY_DELAY` | `20` / `2.0` | 启动重连次数与间隔（秒） |
| 向量库 | `VECTOR_BACKEND` | `milvus` | `milvus` / `off`（关闭后纯 BM25） |
| | `MILVUS_HOST` / `MILVUS_PORT` | `127.0.0.1` / `19530` | Milvus 地址；Compose 内为服务名 `milvus` |
| | `MILVUS_COLLECTION` | `yy_knowledge_chunks` | 集合名，换维度需改名或 drop 重建 |
| | `EMBED_DIM` | `1024` | 必须与 embedding 模型输出维度一致（bge-m3 / text-embedding-v3 为 1024，nomic 为 768） |
| | `MILVUS_TOPK` | `30` | 向量召回候选数 |
| 对象存储 | `STORAGE_BACKEND` | `minio` | `minio` / `local`（失败自动降级本地磁盘） |
| | `MINIO_ENDPOINT` | `127.0.0.1:9000` | MinIO 地址 |
| | `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | `minioadmin` | 访问密钥 |
| | `MINIO_BUCKET` / `MINIO_SECURE` | `youyu-uploads` / `false` | 私有桶名 / 是否 HTTPS |
| | `UPLOAD_DIR` / `MAX_UPLOAD_SIZE` | `uploads` / `10485760` | 本地降级目录 / 单文件上限（字节） |
| AI 主链路 | `LLM_FRAMEWORK` | `langchain` | `langchain` / `httpx`（直连兜底） |
| | `LLM_TIMEOUT` | `30.0` | 模型调用超时（秒） |
| 检索切块 | `CHUNK_SIZE` / `CHUNK_OVERLAP` | `300` / `60` | 切片窗口与重叠字数 |
| 安全 | `SECRET_KEY` | `change-this-secret-in-production` | JWT 签名密钥，生产必改 |
| | `TOKEN_EXPIRE_MINUTES` | `10080` | Token 有效期（7 天） |
| | `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | 允许的前端来源 |

---

## 十、API 一览

> 全部路由统一挂载在 `/api` 前缀下；完整 OpenAPI 文档见 `http://localhost:8000/docs`。

| 模块 | 方法 | 端点 | 描述 |
|:---|:---|:---|:---|
| 认证 | `POST` | `/api/auth/register` | 注册 |
| | `POST` | `/api/auth/login` | 登录，返回 JWT |
| | `GET` | `/api/auth/me` | 当前用户 |
| 商城 | `GET` | `/api/categories` | 分类列表 |
| | `GET` / `POST` / `PUT` / `DELETE` | `/api/products`、`/api/products/{id}` | 商品（分页 / 搜索 / 排序 / 上下架） |
| | `GET` | `/api/products/{id}/similar` | 相似推荐 |
| | `POST` / `DELETE` | `/api/favorites`、`/api/favorites/{id}` | 收藏 |
| 交易 | `GET` / `POST` / `PUT` / `DELETE` | `/api/cart` | 购物车（勾选、批量删、清空） |
| | `POST` / `GET` | `/api/orders` | 下单结算 / 订单中心 |
| | `PUT` | `/api/orders/{id}/status` | 支付 / 发货 / 收货 / 取消 |
| | `GET` / `POST` | `/api/reviews` | 评价 |
| 内容 | `GET` / `POST` / `PUT` / `DELETE` | `/api/news`、`/api/banners`、`/api/notices` | 资讯 / 轮播 / 公告 |
| | `POST` | `/api/upload` | 图片上传（返回 wangEditor 协议 `{errno, data:[{url}]}`） |
| | `GET` | `/api/files/{object_path:path}` | 代理读取 MinIO 私有桶；本地降级时返回 `/uploads/{name}` |
| 后台 | `GET` / `POST` / `PUT` / `DELETE` | `/api/admin/admins`、`/api/admin/members` | 管理员 / 会员 |
| | `GET` | `/api/admin/dashboard` | ECharts：订单状态、分类占比、热销 Top10、核心指标 |
| | `GET` / `PUT` | `/api/admin/orders`、`/api/admin/orders/{id}/status` | 全量订单与状态流转 |
| | `GET` | `/api/admin/reviews` | 全量评价 |
| AI 能力中心（需管理员） | `CRUD` | `/api/ai/models` | 对话 / 向量 / 图片模型，启停、默认、多模态标记 |
| | `POST` | `/api/ai/models/{id}/test` | 测试连接 |
| | `CRUD` | `/api/ai/prompts` | 7 类提示词 |
| | `POST` | `/api/ai/prompts/{id}/preview` | 变量渲染预览 |
| | `CRUD` | `/api/knowledge/docs` | 知识库文档 + 自动切片 + 写 Milvus |
| | `GET` | `/api/knowledge/docs/{id}/chunks` | 切片预览（`has_vector` 查 Milvus） |
| | `POST` | `/api/knowledge/docs/{id}/reindex` | 重建索引 |
| | `POST` | `/api/knowledge/search-test` | 检索测试 |
| 对话 | `POST` | `/api/chat/stream` | SSE 流式（文本 + 图片） |
| | `GET` | `/api/chat/sessions` | 会话列表 |
| | `GET` | `/api/chat/sessions/{id}/messages` | 完整消息与执行轨迹 |
| | `GET` | `/api/admin/chat/records` | 后台全链路记录 |

> 统一响应：`{"code":0,"msg":"success","data":...}`；越权 401、参数错误 400、未找到 404。

---

## 十一、项目结构

```
youyu-fishing/
├── README.md                          # 项目说明（本文）
├── 项目说明文档.md                     # 目录结构、接口清单、工程要点与边界
├── docker-compose.yml                 # 一键部署（MySQL / etcd / MinIO / Milvus / backend）
├── .gitignore
│
├── backend/
│   ├── requirements.txt               # FastAPI / Tortoise / pymilvus / minio / LangChain / LangGraph
│   ├── Dockerfile / .dockerignore
│   ├── .env.example                   # 全部配置项（见 §九）
│   ├── uploads/                       # MinIO 不可用时的本地降级目录（运行时生成）
│   ├── static/demo/                   # 商品 / 轮播演示占位素材（SVG）
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口：CORS、全局异常、路由注册、基础设施、种子数据
│   │   ├── config.py                  # 配置中心（DATABASE_URL / VECTOR_BACKEND / STORAGE_BACKEND / LLM_FRAMEWORK）
│   │   ├── database.py                # Tortoise + MySQL 初始化、退避重连、自动建表
│   │   ├── result.py / schemas.py     # 统一响应 Result / Pydantic 出入参
│   │   ├── models.py / seed.py        # ORM 模型 / 演示种子数据
│   │   ├── deps.py                    # JWT 签发解析 + user / admin 依赖
│   │   ├── api/                       # auth · shop · trade · cms · admin · ai_config · knowledge · chat
│   │   ├── agent/                     # state · prompts · tools · nodes · graph（StateGraph + 顺序兜底）
│   │   ├── rag/                       # chunker（300/60）· embeddings · retriever（向量 + BM25 + RRF）
│   │   ├── llm/                       # factory（LangChain + httpx 兜底）· vision
│   │   └── infra/                     # milvus_client · minio_client（失败自动降级）
│   └── tests/                         # test_chunker · test_retriever · test_infra
│
└── frontend/
    ├── package.json / vite.config.ts / index.html
    └── src/
        ├── main.ts / App.vue
        ├── router/                    # 路由 + 前后台守卫
        ├── api/                       # Axios 拦截器 + token + SSE、全部接口封装
        ├── stores/ / utils/           # 购物车状态、事件总线、markdown-it 渲染
        ├── components/                # ProductCard · AiBubble · RichEditor · EChart
        ├── views/front/               # 首页 · 商品 · 详情 · 购物车 · 结算 · 订单 · 资讯 · AI 助手 · 登录
        └── views/admin/               # 看板 · 各类管理 · 模型 · 提示词 · 知识库 · 对话记录
```

**文档导航**

| 文档 | 内容 |
|:---|:---|
| `README.md`（本文） | 项目总览、架构、快速开始、环境变量、API、测试与边界 |
| `项目说明文档.md` | 逐文件目录说明、完整接口清单、Agent 工作流、10 条关键工程点、演示数据与 TODO |
| `backend/.env.example` | 全量环境变量模板 |
| `docker-compose.yml` | 五服务编排与健康检查配置 |

---

## 十二、参与贡献

有渔渔具是一个用于演示「AI Agent 如何真正接进电商业务」的公开项目，欢迎提交 Issue 或 Pull Request：

- 🎣 **渔具 / 垂钓从业者** — 补充选竿知识库语料、修正参数与场景口径
- 🧠 **AI 应用开发者** — 新增意图分支、工具与模型适配，优化 RAG 召回与降级策略
- 💻 **前后端开发者** — 完善商城交互、后台配置体验与流式渲染细节
- 📝 **文档贡献者** — 补充界面截图、部署实践与各厂商模型接入示例

提交前建议先跑 `cd backend; python -m pytest`，并在 PR 中说明改动涉及的链路与验证方式。

---

## 十三、免责声明与许可证

### 免责声明

本项目为**学习与演示用途**的 AI Agent 商城示例：

- 支付为状态机模拟，未接入真实支付网关；短信 / 邮件未接入，请勿用于真实交易。
- AI 回答由大模型基于知识库与商品数据生成，仅供参考，**不构成专业垂钓装备选购或投资建议**，请以商品实际参数与商家说明为准。
- 模型 API Key 等敏感配置仅存放于本地 `.env` 或后台配置，请勿提交到公开仓库。

### 许可证

仓库当前**未附带 LICENSE 文件**，暂未声明开源许可证；在维护者补充授权前，本项目仅作为学习与演示用途。如需商用或二次分发，请先与仓库维护者确认授权。

---

<p align="center">
  <strong>✨ 让 AI 不只是回答问题，而是把生意跑完一轮</strong>
</p>
