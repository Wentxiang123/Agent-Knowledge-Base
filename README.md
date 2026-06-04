# Agent Knowledge Base

A semantic knowledge base with streaming retrieval and MCP integration for agents.

## Overview

This project implements a lightweight knowledge base service that supports text ingestion, semantic search, streaming responses, and an MCP tool interface for agent workflows.

## Current Status

Implemented:

- Project structure
- SQLite database connection
- SQLAlchemy data models for knowledge bases, documents, and chunks
- Knowledge base CRUD API
- Pagination for knowledge base listing

Planned:

- Text and txt document upload
- Text chunking
- Embedding generation
- Vector store integration
- Semantic search
- Streaming search response
- MCP tool integration

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

## Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

After startup, open the API docs at:

```text
http://127.0.0.1:8000/docs
```
