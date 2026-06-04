"""Semantic search service."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import SearchResult
from app.services import kb_service
from app.services.embedding_service import embedding_service
from app.services.vector_store_service import get_vector_store_service


def _normalize_query(query: str | None) -> str:
    if query is None:
        return ""
    return " ".join(query.strip().split())


def _score_from_distance(distance: float) -> float:
    return max(0.0, min(1.0, 1.0 - distance))


def _first_result_list(raw: dict[str, Any], key: str) -> list[Any]:
    value = raw.get(key) or []
    if not value:
        return []
    first = value[0]
    return first if isinstance(first, list) else []


def _build_results(raw: dict[str, Any]) -> list[SearchResult]:
    documents = _first_result_list(raw, "documents")
    metadatas = _first_result_list(raw, "metadatas")
    distances = _first_result_list(raw, "distances")

    results: list[SearchResult] = []
    for content, metadata, distance in zip(documents, metadatas, distances):
        if not isinstance(metadata, dict):
            continue
        distance_value = float(distance)
        results.append(
            SearchResult(
                kb_id=int(metadata["kb_id"]),
                document_id=int(metadata["document_id"]),
                chunk_id=int(metadata["chunk_id"]),
                chunk_index=int(metadata["chunk_index"]),
                title=str(metadata.get("title") or "Untitled Document"),
                content=str(content),
                score=round(_score_from_distance(distance_value), 4),
                distance=round(distance_value, 4),
            )
        )
    return results


def search_knowledge_base(
    db: Session,
    query: str,
    top_k: int = 5,
    knowledge_base_id: int | None = None,
) -> list[SearchResult]:
    normalized_query = _normalize_query(query)
    if not normalized_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="query cannot be empty",
        )
    if knowledge_base_id is not None:
        kb_service.get_knowledge_base(db, knowledge_base_id)

    query_embedding = embedding_service.embed_text(normalized_query)
    raw_results = get_vector_store_service().query(
        query_embedding=query_embedding,
        top_k=top_k,
        kb_id=knowledge_base_id,
    )
    return _build_results(raw_results)
