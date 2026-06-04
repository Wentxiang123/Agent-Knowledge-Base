"""Pydantic request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class KnowledgeBaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseList(BaseModel):
    items: list[KnowledgeBaseRead]
    total: int
    page: int
    page_size: int


class DocumentTextCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kb_id: int
    document_id: int
    content: str
    chunk_index: int
    vector_id: str | None
    created_at: datetime


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kb_id: int
    title: str
    content: str
    created_at: datetime


class DocumentIngestResponse(BaseModel):
    document: DocumentRead
    chunks: list[ChunkRead]
    chunk_count: int


class SearchResult(BaseModel):
    kb_id: int
    document_id: int
    chunk_id: int
    chunk_index: int
    title: str
    content: str
    score: float
    distance: float


class SearchResponse(BaseModel):
    query: str
    knowledge_base_id: int | None
    top_k: int
    results: list[SearchResult]
