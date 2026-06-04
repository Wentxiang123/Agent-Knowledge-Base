from fastapi import HTTPException

from app import mcp_server
from app.schemas import SearchResult


def test_run_knowledge_base_search_returns_results(monkeypatch) -> None:
    def fake_search_knowledge_base(db, query, top_k, knowledge_base_id):
        return [
            SearchResult(
                kb_id=1,
                document_id=2,
                chunk_id=3,
                chunk_index=0,
                title="春",
                content="春天的脚步近了。",
                score=0.91,
                distance=0.09,
            )
        ]

    monkeypatch.setattr(mcp_server.search_service, "search_knowledge_base", fake_search_knowledge_base)

    payload = mcp_server.run_knowledge_base_search(query="春天", knowledge_base_id=1, top_k=1)

    assert payload["ok"] is True
    assert payload["query"] == "春天"
    assert payload["knowledge_base_id"] == 1
    assert payload["top_k"] == 1
    assert payload["results"][0]["title"] == "春"


def test_run_knowledge_base_search_returns_validation_error() -> None:
    payload = mcp_server.run_knowledge_base_search(query="春天", top_k=0)

    assert payload["ok"] is False
    assert payload["status_code"] == 400
    assert payload["error"] == "top_k must be between 1 and 20"


def test_run_knowledge_base_search_maps_http_errors(monkeypatch) -> None:
    def fake_search_knowledge_base(db, query, top_k, knowledge_base_id):
        raise HTTPException(status_code=404, detail="knowledge base not found")

    monkeypatch.setattr(mcp_server.search_service, "search_knowledge_base", fake_search_knowledge_base)

    payload = mcp_server.run_knowledge_base_search(query="春天", knowledge_base_id=999, top_k=3)

    assert payload["ok"] is False
    assert payload["status_code"] == 404
    assert payload["error"] == "knowledge base not found"
