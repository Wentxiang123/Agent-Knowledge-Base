# 运行说明与实现思路

本文档用于说明本项目的本地运行方式、核心接口验证流程、MCP Tool 启动方式以及整体实现思路。

## 1. 项目简介

本项目实现了一个支持语义检索的知识库系统，主要能力包括：

- 知识库增删改查，支持分页查询。
- 支持直接输入文本或上传 `.txt` 文件。
- 文本上传后自动切分为 chunk。
- 为 chunk 生成 embedding，并写入 Chroma 向量库。
- 支持基于自然语言 query 的语义检索。
- 支持普通 JSON 搜索返回和流式文本返回。
- 将搜索能力封装为 MCP Tool，供 Agent 调用。

## 2. 技术栈

- FastAPI：提供 HTTP API。
- SQLite：保存知识库、文档和 chunk 元数据。
- SQLAlchemy：管理数据库模型和会话。
- Chroma：保存文本 chunk 的向量数据。
- httpx：调用 OpenAI-compatible embedding 接口。
- MCP Python SDK：封装 Agent 可调用的 MCP Tool。
- pytest：基础自动化测试。

## 3. 目录结构

```text
app/
  main.py                 # FastAPI API 入口
  database.py             # SQLite 连接和 Session 管理
  models.py               # SQLAlchemy 数据模型
  schemas.py              # Pydantic 请求和响应结构
  mcp_server.py           # MCP Server 和 tool 定义
  services/
    kb_service.py         # 知识库 CRUD
    document_service.py   # 文本上传、txt 解析、文本切分
    embedding_service.py  # embedding 生成
    vector_store_service.py # Chroma 写入和查询
    search_service.py     # 语义检索和流式结果格式化

data/
  uploads/                # 上传的 txt 原文件
  vector_store/           # Chroma 持久化目录

docs/
  technical-design.md
  run-and-implementation.md

tests/
  test_knowledge_bases.py
  test_documents.py
  test_embedding_service.py
  test_search.py
  test_mcp_server.py
```

## 4. 环境准备

建议使用 Python 3.11 或以上版本。

### 4.1 克隆仓库

```bash
git clone https://github.com/Wentxiang123/Agent-Knowledge-Base.git
cd Agent-Knowledge-Base
```

### 4.2 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
python -m venv .venv
source .venv/bin/activate
```

### 4.3 安装依赖

```bash
pip install -r requirements.txt
```

### 4.4 配置环境变量

可以复制 `.env.example` 为 `.env`，也可以直接使用默认值运行。

```text
DATABASE_URL=sqlite:///./data/app.db
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIRECTORY=./data/vector_store
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
EMBEDDING_MODEL=
REQUEST_TIMEOUT_SECONDS=30
```

如果配置了 `EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL` 和 `EMBEDDING_MODEL`，系统会调用兼容 OpenAI `/v1/embeddings` 格式的接口。

如果没有配置以上三个变量，系统会使用本地确定性 embedding 兜底，方便在无外部 API key 的环境下完成基础演示和测试。正式语义效果建议配置真实 embedding 模型。

## 5. 启动 API 服务

```bash
uvicorn app.main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

## 6. 接口验证流程

下面是一条完整的验证链路：创建知识库 -> 上传文本 -> 查询相关内容。

### 6.1 创建知识库

```bash
curl -X POST "http://127.0.0.1:8000/knowledge-bases" \
  -H "Content-Type: application/json" \
  -d '{"name":"文学作品","description":"用于测试语义检索"}'
```

记录返回结果中的 `id`，后续示例假设知识库 ID 为 `1`。

### 6.2 分页查询知识库

```bash
curl "http://127.0.0.1:8000/knowledge-bases?page=1&page_size=10"
```

### 6.3 直接上传文本

```bash
curl -X POST "http://127.0.0.1:8000/knowledge-bases/1/documents/text" \
  -H "Content-Type: application/json" \
  -d '{"title":"春","content":"春天来了，东风来了，山朗润起来了，水涨起来了，太阳的脸红起来了。"}'
```

上传后系统会执行：

```text
保存原始文档
-> 切分文本 chunk
-> 生成 embedding
-> 写入 Chroma
-> 回写 chunk.vector_id
```

### 6.4 上传 txt 文件

```bash
curl -X POST "http://127.0.0.1:8000/knowledge-bases/1/documents/file" \
  -F "title=故乡" \
  -F "file=@./guxiang.txt"
```

`.txt` 文件解析支持：

- UTF-8
- UTF-8 with BOM
- GB18030

### 6.5 普通语义搜索

```bash
curl "http://127.0.0.1:8000/search?query=春天&knowledge_base_id=1&top_k=5"
```

返回示例：

```json
{
  "query": "春天",
  "knowledge_base_id": 1,
  "top_k": 5,
  "results": [
    {
      "kb_id": 1,
      "document_id": 1,
      "chunk_id": 1,
      "chunk_index": 0,
      "title": "春",
      "content": "相关文本片段...",
      "score": 0.92,
      "distance": 0.08
    }
  ]
}
```

### 6.6 流式语义搜索

```bash
curl -N "http://127.0.0.1:8000/search/stream?query=春天&knowledge_base_id=1&top_k=5"
```

返回内容会以 `text/plain` 的方式逐段输出，例如：

```text
正在查询知识库：春天
找到 1 条相关内容。

[1] 春
相关度：0.92
来源：知识库 1，文档 1，片段 0
相关片段：相关文本片段...
```

## 7. MCP Tool 运行说明

启动 MCP Server：

```bash
python -m app.mcp_server
```

MCP Server 暴露一个工具：

```text
search_knowledge_base
```

输入参数：

```json
{
  "query": "帮我查一下春天相关内容",
  "knowledge_base_id": 1,
  "top_k": 3
}
```

输出示例：

```json
{
  "ok": true,
  "query": "帮我查一下春天相关内容",
  "knowledge_base_id": 1,
  "top_k": 3,
  "results": [
    {
      "kb_id": 1,
      "document_id": 1,
      "chunk_id": 1,
      "chunk_index": 0,
      "title": "春",
      "content": "相关文本片段...",
      "score": 0.92,
      "distance": 0.08
    }
  ]
}
```

MCP client 配置示例：

```json
{
  "mcpServers": {
    "agent-knowledge-base": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "env": {
        "DATABASE_URL": "sqlite:///./data/app.db",
        "CHROMA_PERSIST_DIRECTORY": "./data/vector_store"
      }
    }
  }
}
```

Agent 调用链路示例：

```text
用户：帮我查一下春天相关内容
Agent：调用 search_knowledge_base
MCP Tool：在知识库中检索 query 相关文本片段
Agent：根据 tool 返回内容整理最终回答
```

## 8. 测试说明

运行测试：

```bash
pytest
```

当前测试覆盖：

- 知识库创建、查询、更新、删除。
- 文本上传、txt 上传、中文编码解析。
- 文本切分和 chunk vector_id 回写。
- embedding 本地兜底逻辑。
- 普通语义搜索。
- 流式语义搜索。
- MCP Tool 包装层和错误映射。

## 9. 实现思路说明

### 9.1 知识库管理

系统使用 SQLite 保存结构化数据。`knowledge_bases` 表保存知识库信息，`documents` 表保存上传的原始文本，`chunks` 表保存切分后的文本片段以及对应的 `vector_id`。

知识库 CRUD 通过 FastAPI 接口暴露，并在服务层 `kb_service.py` 中统一处理，避免路由函数直接操作业务细节。

### 9.2 文本上传与切分

系统支持两类上传方式：

- 直接提交文本。
- 上传 `.txt` 文件。

`.txt` 文件会先进行后缀校验和编码解析，再保存原始文件。文本内容会按照固定长度切分为 chunk，默认每 500 字一段，相邻 chunk 重叠 50 字。这样既能控制每段文本长度，也能减少边界处信息丢失。

### 9.3 Embedding 生成

上传后的每个 chunk 都会生成 embedding。

如果配置了兼容 OpenAI 格式的 embedding 服务，系统会调用远程 `/v1/embeddings` 接口。否则系统使用本地确定性 embedding 兜底，保证项目在没有外部服务的情况下也能启动、测试和演示完整链路。

### 9.4 向量库写入

系统使用 Chroma 作为向量数据库。每个 chunk 写入 Chroma 时会携带 metadata：

```text
kb_id
document_id
chunk_id
chunk_index
title
```

这样检索命中后可以直接知道结果来自哪个知识库、哪个文档和哪个文本片段。

### 9.5 语义检索

用户输入 query 后，系统会先对 query 生成 embedding，然后在 Chroma 中做相似度检索，返回 top_k 个最相关文本片段。

如果传入 `knowledge_base_id`，检索会限定在指定知识库内；如果不传，则在全部知识库中检索。

### 9.6 流式返回

流式接口复用普通搜索逻辑，先完成检索，再通过 FastAPI `StreamingResponse` 将文本结果切成小段输出。

这样可以模拟类似 DeepSeek / ChatGPT 的逐步输出效果，同时保持搜索逻辑只有一份，减少普通搜索和流式搜索结果不一致的风险。

### 9.7 MCP Tool 封装

MCP 层将语义搜索能力封装成 `search_knowledge_base` tool。Agent 只需要传入 query，即可调用该工具查询知识库。

MCP 工具内部复用 `search_service.py`，不会重复实现搜索逻辑。工具返回结构化 JSON，方便 Agent 后续整理回答。

### 9.8 错误处理

系统对常见错误做了处理：

- query 为空。
- 知识库不存在。
- 上传内容为空。
- 上传文件不是 `.txt`。
- txt 文件编码解析失败。
- embedding 服务失败。
- 向量库写入或检索失败。
- MCP tool 参数非法。

API 层通过 HTTP 状态码返回错误；MCP Tool 层通过 `{ "ok": false, "error": "..." }` 的结构返回错误，方便 Agent 理解。

## 10. 提交说明建议

最终提交时建议包含：

```text
Agent-Knowledge-Base/
  app/
  data/
  docs/
  tests/
  README.md
  requirements.txt
  .env.example
  个人简历
```

邮件或压缩包命名可按笔试要求整理为：

```text
姓名-学校-2026-06-04-Agent
```
