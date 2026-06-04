# Agent Knowledge Base 技术方案

## 1. 项目目标

本项目实现一个支持语义检索的知识库系统。用户可以创建知识库、上传文本内容，并通过自然语言 query 查询相关知识内容。系统同时提供流式搜索接口，并将知识库查询能力封装为 MCP Tool，使 Agent 能够调用该能力完成知识检索任务。

## 2. 核心功能

- 知识库增删改查，支持分页。
- 支持上传知识内容，至少支持 txt 文件或直接输入文本。
- 支持语义相关性查询。
- 查询结果支持流式返回。
- 将查询能力封装为 Agent 可调用的 MCP Tool。
- 提供 README、运行说明和实现思路说明。

## 3. 技术栈

- 后端框架：FastAPI
- 数据库：SQLite
- ORM：SQLAlchemy
- 向量库：Chroma
- Embedding：兼容 OpenAI 格式的 embedding API 或本地 embedding 模型
- MCP：Python MCP SDK
- 流式返回：FastAPI StreamingResponse

## 4. 模块划分

```text
app/
  main.py                 # FastAPI 入口
  database.py             # 数据库连接
  models.py               # 数据表模型
  schemas.py              # 请求和响应结构
  services/
    kb_service.py         # 知识库 CRUD
    document_service.py   # 文档上传和文本切分
    embedding_service.py  # 文本向量化
    search_service.py     # 语义检索
  mcp_server.py           # MCP Tool 服务
```

## 5. 数据模型

### knowledge_bases

```text
id
name
description
created_at
updated_at
```

### documents

```text
id
kb_id
title
content
created_at
```

### chunks

```text
id
kb_id
document_id
content
chunk_index
vector_id
created_at
```

## 6. 文本处理流程

```text
接收文本或 txt 文件
-> 校验知识库是否存在
-> 保存原始文档
-> 文本切分为 chunks
-> 生成 chunk embedding
-> 写入向量数据库
-> 保存 chunk 元数据
```

默认切分策略：每 500 字一段，重叠 50 字。

## 7. 语义检索流程

```text
query
-> 生成 query embedding
-> 在向量库中相似度搜索
-> 获取 top_k 个结果
-> 返回知识库、文档标题、文本片段和相似度分数
```

## 8. API 设计

```text
POST   /knowledge-bases
GET    /knowledge-bases?page=1&page_size=10
GET    /knowledge-bases/{kb_id}
PUT    /knowledge-bases/{kb_id}
DELETE /knowledge-bases/{kb_id}

POST /knowledge-bases/{kb_id}/documents/text
POST /knowledge-bases/{kb_id}/documents/file

GET /search?query=春天&top_k=5
GET /search/stream?query=春天&top_k=5
```

## 9. MCP Tool 设计

工具名：`search_knowledge_base`

输入参数：

```json
{
  "query": "帮我查一下春天相关内容",
  "knowledge_base_id": 1,
  "top_k": 3
}
```

输出结果：

```json
{
  "results": [
    {
      "title": "春",
      "content": "相关文本片段...",
      "score": 0.89
    }
  ]
}
```

## 10. 错误处理

需要覆盖：

- query 为空
- 知识库不存在
- 上传内容为空
- 上传文件不是 txt
- embedding 服务调用失败
- 向量库检索失败
- 没有检索结果
- MCP Tool 调用超时
