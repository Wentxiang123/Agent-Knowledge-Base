"""Chroma vector store integration."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from fastapi import HTTPException, status

from app import models

COLLECTION_NAME = "knowledge_chunks"


class VectorStoreService:
    def __init__(self) -> None:
        persist_directory = Path(os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/vector_store"))
        persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        chunks: list[models.Chunk],
        embeddings: list[list[float]],
        document: models.Document,
    ) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        ids = [chunk.vector_id or f"chunk-{chunk.id}" for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "kb_id": chunk.kb_id,
                "document_id": chunk.document_id,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "title": document.title,
            }
            for chunk in chunks
        ]

        try:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"vector store upsert failed: {exc}",
            ) from exc

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        kb_id: int | None = None,
    ) -> dict[str, Any]:
        where = {"kb_id": kb_id} if kb_id is not None else None
        try:
            return self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"vector store query failed: {exc}",
            ) from exc


@lru_cache(maxsize=1)
def get_vector_store_service() -> VectorStoreService:
    return VectorStoreService()
