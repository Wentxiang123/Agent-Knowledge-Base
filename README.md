# Agent Knowledge Base

一个支持语义检索、流式返回和 MCP Tool 集成的知识库系统。

## 项目简介

本项目实现了一个轻量级知识库服务，支持创建知识库、上传文本或 `.txt` 文件、自动切分文本、生成 embedding、写入 Chroma 向量库，并通过普通搜索、流式搜索和 MCP Tool 对外提供查询能力。

更完整的运行步骤、验证流程和实现思路见：[docs/run-and-implementation.md](docs/run-and-implementation.md)。

## 当前功能

已实现：

- 中文可视化操作页面
- 创建、查看、删除知识库
- SQLite 数据库连接
- 知识库、文档、文本片段的 SQLAlchemy 数据模型
- 知识库增删改查 API
- 直接文本上传
- `.txt` 文件解析，支持 UTF-8 和 GB18030
- 固定长度 + 重叠窗口的文本切分
- 兼容 OpenAI 格式的 embedding 生成
- 本地确定性 embedding 兜底，便于开发和演示
- Chroma 向量库集成
- 删除知识库时同步清理对应向量数据
- 文档上传后自动向量化并写入向量库
- 语义搜索 API
- 流式搜索返回
- MCP Tool 集成
- 知识库 CRUD、文档上传、embedding、搜索、MCP Tool 测试

## 可视化页面

本地启动后，优先访问中文可视化页面：

```text
http://127.0.0.1:8000/
```

页面包含：

- 创建知识库
- 上传文章内容
- 上传 `.txt` 文件
- 普通搜索
- 流式搜索
- 知识库列表
- 删除知识库

接口调试文档仍然保留：

```text
http://127.0.0.1:8000/docs
```

## API 接口

### 健康检查

```text
GET /health
```

### 知识库管理

```text
POST   /knowledge-bases
GET    /knowledge-bases?page=1&page_size=10
GET    /knowledge-bases/{kb_id}
PUT    /knowledge-bases/{kb_id}
DELETE /knowledge-bases/{kb_id}
```

### 文档上传

```text
POST /knowledge-bases/{kb_id}/documents/text
POST /knowledge-bases/{kb_id}/documents/file
```

直接上传文本示例：

```json
{
  "title": "春",
  "content": "盼望着，盼望着，东风来了，春天的脚步近了。"
}
```

`.txt` 文件上传接口使用 multipart form data：

```text
file  = .txt 文件
title = 可选，文档标题
```

### 语义搜索

```text
GET /search?query=春天&knowledge_base_id=1&top_k=5
```

如果不传 `knowledge_base_id`，会在全部知识库中搜索。

### 流式搜索

```text
GET /search/stream?query=春天&knowledge_base_id=1&top_k=5
```

流式接口返回 `text/plain` 小段文本，适合演示 Agent 边检索边输出的效果。

## MCP Tool

启动 MCP Server：

```bash
python -m app.mcp_server
```

暴露的工具名：

```text
search_knowledge_base
```

工具输入示例：

```json
{
  "query": "帮我查一下春天相关内容",
  "knowledge_base_id": 1,
  "top_k": 3
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

## 环境变量

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

如果没有配置以上三个变量，系统会使用本地确定性 embedding 兜底，保证项目在没有外部服务的情况下也能启动、测试和演示完整链路。

## 本地运行

进入项目目录后执行：

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Windows PowerShell 如果使用虚拟环境，可以这样启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000/
```

## 运行测试

```bash
pytest
```
