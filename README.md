# Agent Knowledge Base

A semantic knowledge base with streaming retrieval and MCP integration for agents.

## Overview

This project implements a lightweight knowledge base service that supports text ingestion, semantic search, streaming responses, and an MCP tool interface for agent workflows.

For detailed setup, validation steps, and implementation notes, see [docs/run-and-implementation.md](docs/run-and-implementation.md).

## Current Status

Implemented:

- Project structure
- SQLite database connection
- SQLAlchemy data models for knowledge bases, documents, and chunks
- Knowledge base CRUD API
- Pagination for knowledge base listing
- Text document upload
- txt file parsing with UTF-8 and GB18030 support
- Text chunking with fixed-size overlap
- Embedding generation with OpenAI-compatible API support
- Local deterministic embedding fallback for development and tests
- Chroma vector store integration
- Automatic vector indexing after document ingestion
- Semantic search API
- Streaming search response
- MCP tool integration
- CRUD tests for knowledge base endpoints
- Document ingestion tests
- Embedding service tests
- Semantic search tests
- MCP tool tests

## API Endpoints

### Health Check

```text
GET /health
```

### Knowledge Bases

```text
POST   /knowledge-bases
GET    /knowledge-bases?page=1&page_size=10
GET    /knowledge-bases/{kb_id}
PUT    /knowledge-bases/{kb_id}
DELETE /knowledge-bases/{kb_id}
```

### Documents

```text
POST /knowledge-bases/{kb_id}/documents/text
POST /knowledge-bases/{kb_id}/documents/file
```

Text upload request example:

```json
{
  "title": "春",
  "content": "盼望着，盼望着，东风来了，春天的脚步近了。"
}
```

The file upload endpoint accepts multipart form data with:

- `file`: a `.txt` file
- `title`: optional document title

After ingestion, each text chunk is embedded and written to Chroma. The generated `vector_id` is stored back on the chunk record.

### Search

```text
GET /search?query=春天&knowledge_base_id=1&top_k=5
```

Response example:

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

### Streaming Search

```text
GET /search/stream?query=春天&knowledge_base_id=1&top_k=5
```

The streaming endpoint returns `text/plain` chunks such as:

```text
正在查询知识库：春天
找到 1 条相关内容。

[1] 春
相关度：0.92
来源：知识库 1，文档 1，片段 0
相关片段：相关文本片段...
```

## MCP Tool

Start the MCP server with:

```bash
python -m app.mcp_server
```

It exposes one tool:

```text
search_knowledge_base
```

Tool input:

```json
{
  "query": "帮我查一下春天相关内容",
  "knowledge_base_id": 1,
  "top_k": 3
}
```

Tool output:

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

Example MCP client configuration:

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

## Environment Variables

```text
DATABASE_URL=sqlite:///./data/app.db
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIRECTORY=./data/vector_store
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
EMBEDDING_MODEL=
REQUEST_TIMEOUT_SECONDS=30
```

If `EMBEDDING_API_KEY`, `EMBEDDING_BASE_URL`, and `EMBEDDING_MODEL` are all configured, the service calls an OpenAI-compatible `/v1/embeddings` endpoint. Otherwise, it uses a local deterministic embedding fallback so the project can run without external credentials.

## Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

After startup, open the API docs at:

```text
http://127.0.0.1:8000/docs
```

## Run Tests

```bash
pytest
```
