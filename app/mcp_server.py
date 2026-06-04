"""MCP server entry point for agent tool integration."""

from typing import Any

from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP

from app.database import Base, SessionLocal, engine
from app.services import search_service

mcp = FastMCP("agent-knowledge-base")


def _result_to_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return dict(result)


def _error_response(message: str, status_code: int = 500) -> dict[str, Any]:
    return {
        "ok": False,
        "error": message,
        "status_code": status_code,
        "results": [],
    }


def run_knowledge_base_search(
    query: str,
    knowledge_base_id: int | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """Run semantic search and return an MCP-friendly payload."""
    if top_k < 1 or top_k > 20:
        return _error_response("top_k must be between 1 and 20", status_code=400)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        results = search_service.search_knowledge_base(
            db=db,
            query=query,
            top_k=top_k,
            knowledge_base_id=knowledge_base_id,
        )
        return {
            "ok": True,
            "query": query.strip(),
            "knowledge_base_id": knowledge_base_id,
            "top_k": top_k,
            "results": [_result_to_dict(result) for result in results],
        }
    except HTTPException as exc:
        return _error_response(str(exc.detail), status_code=exc.status_code)
    except TimeoutError:
        return _error_response("tool call timed out", status_code=504)
    except Exception as exc:
        return _error_response(f"knowledge base search failed: {exc}", status_code=500)
    finally:
        db.close()


@mcp.tool()
def search_knowledge_base(
    query: str,
    knowledge_base_id: int | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """Search the semantic knowledge base for content related to a query.

    Args:
        query: Natural language search text.
        knowledge_base_id: Optional knowledge base ID to search within.
        top_k: Maximum number of related chunks to return. Must be between 1 and 20.
    """
    return run_knowledge_base_search(
        query=query,
        knowledge_base_id=knowledge_base_id,
        top_k=top_k,
    )


if __name__ == "__main__":
    mcp.run()
