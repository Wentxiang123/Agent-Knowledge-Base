# Agent 集成方案说明

## 选择方案

笔试要求中给出的方向是：基于 OpenClaw / Claude Code / Hermas Agent，将第一部分实现的知识库查询能力封装为 skill 或 MCP tool / MCP server。

本项目选择的是：

```text
Claude Code + MCP Server
```

也就是说，本项目没有选择 OpenClaw 或 Hermas Agent，也没有选择 skill 方案，而是将知识库查询能力封装成一个 MCP Server，并在其中暴露一个可被 Agent 调用的 MCP Tool。

## 体现位置

### 1. MCP Server 入口

```text
app/mcp_server.py
```

该文件中创建了 MCP Server：

```python
mcp = FastMCP("agent-knowledge-base")
```

并暴露了工具：

```python
@mcp.tool()
def search_knowledge_base(...):
    ...
```

这就是 Agent 可以调用的知识库查询工具。

### 2. Tool 名称

```text
search_knowledge_base
```

该工具支持输入：

```json
{
  "query": "帮我查一下春天相关内容",
  "knowledge_base_id": 1,
  "top_k": 3
}
```

返回相关知识库内容：

```json
{
  "ok": true,
  "query": "帮我查一下春天相关内容",
  "knowledge_base_id": 1,
  "top_k": 3,
  "results": [
    {
      "title": "春",
      "content": "相关文本片段...",
      "score": 0.92
    }
  ]
}
```

### 3. 启动方式

```bash
python -m app.mcp_server
```

### 4. MCP client 配置示例

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

Claude Code 或其他支持 MCP 的 Agent 客户端可以通过该配置启动 MCP Server，并调用 `search_knowledge_base` 工具。

## 调用链路

```text
用户输入问题
-> Claude Code / MCP Agent 判断需要查询知识库
-> 调用 search_knowledge_base 工具
-> MCP Server 调用 search_service.search_knowledge_base
-> Chroma 向量库返回相关 chunk
-> Agent 根据返回结果组织回答
```

## 为什么选择 MCP Server

选择 MCP Server 的原因：

- MCP 是更通用的工具调用协议，适合 Agent 调用外部能力。
- 查询能力可以被 Claude Code 等支持 MCP 的 Agent 直接接入。
- 和第一部分已有的 `search_service.py` 可以复用同一套查询逻辑，避免重复实现。
- 返回结构化 JSON，便于 Agent 进一步整理为自然语言答案。

## 对应笔试要求

笔试要求：

```text
输入 query
查询知识库
返回相关结果
能被 agent 调用
基本错误处理
```

本项目对应实现：

- 输入 query：`search_knowledge_base(query=...)`
- 查询知识库：复用 `app/services/search_service.py`
- 返回相关结果：返回 `results` 数组，包括标题、片段、相关度等信息
- 能被 Agent 调用：通过 `app/mcp_server.py` 暴露 MCP Tool
- 基本错误处理：MCP 层返回 `{ "ok": false, "error": "..." }`
