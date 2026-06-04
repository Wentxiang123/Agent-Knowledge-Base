import os
import shutil
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./data/test_app.db"
os.environ["UPLOAD_DIR"] = "./data/test_uploads"
os.environ["CHROMA_PERSIST_DIRECTORY"] = "./data/test_vector_store"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.services.vector_store_service import get_vector_store_service

client = TestClient(app)


SPRING_TEXT = "春天来了，东风来了，山朗润起来了，水涨起来了，太阳的脸红起来了。"
HOMETOWN_TEXT = "少年闰土在海边看瓜，他项带银圈，手捏一柄钢叉。"


def setup_function() -> None:
    get_vector_store_service.cache_clear()
    shutil.rmtree("./data/test_vector_store", ignore_errors=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module() -> None:
    test_db = Path("./data/test_app.db")
    if test_db.exists():
        test_db.unlink()
    get_vector_store_service.cache_clear()
    shutil.rmtree("./data/test_uploads", ignore_errors=True)
    shutil.rmtree("./data/test_vector_store", ignore_errors=True)


def create_test_knowledge_base() -> int:
    response = client.post(
        "/knowledge-bases",
        json={"name": "文学作品", "description": "测试语义搜索"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def upload_document(kb_id: int, title: str, content: str) -> None:
    response = client.post(
        f"/knowledge-bases/{kb_id}/documents/text",
        json={"title": title, "content": content},
    )
    assert response.status_code == 201


def seed_documents() -> int:
    kb_id = create_test_knowledge_base()
    upload_document(kb_id, "春", SPRING_TEXT)
    upload_document(kb_id, "故乡", HOMETOWN_TEXT)
    return kb_id


def test_search_returns_related_spring_document() -> None:
    kb_id = seed_documents()

    response = client.get(f"/search?query=春天&knowledge_base_id={kb_id}&top_k=2")

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "春天"
    assert data["knowledge_base_id"] == kb_id
    assert data["results"]
    assert data["results"][0]["title"] == "春"
    assert "春天" in data["results"][0]["content"]
    assert 0 <= data["results"][0]["score"] <= 1


def test_search_returns_related_hometown_document() -> None:
    kb_id = seed_documents()

    response = client.get(f"/search?query=少年闰土&knowledge_base_id={kb_id}&top_k=2")

    assert response.status_code == 200
    data = response.json()
    assert data["results"]
    assert data["results"][0]["title"] == "故乡"
    assert "少年闰土" in data["results"][0]["content"]


def test_delete_knowledge_base_removes_vectors_from_search() -> None:
    kb_id = seed_documents()

    delete_response = client.delete(f"/knowledge-bases/{kb_id}")
    search_response = client.get("/search?query=春天&top_k=2")

    assert delete_response.status_code == 204
    assert search_response.status_code == 200
    assert search_response.json()["results"] == []


def test_stream_search_returns_incremental_text() -> None:
    kb_id = seed_documents()

    with client.stream("GET", f"/search/stream?query=春天&knowledge_base_id={kb_id}&top_k=1") as response:
        assert response.status_code == 200
        chunks = list(response.iter_text())

    assert len(chunks) >= 2
    streamed_text = "".join(chunks)
    assert "正在查询知识库：春天" in streamed_text
    assert "找到 1 条相关内容" in streamed_text
    assert "[1] 春" in streamed_text
    assert "相关片段" in streamed_text


def test_search_rejects_blank_query() -> None:
    response = client.get("/search?query=%20%20%20")

    assert response.status_code == 400
    assert response.json()["detail"] == "query cannot be empty"


def test_stream_search_rejects_blank_query() -> None:
    response = client.get("/search/stream?query=%20%20%20")

    assert response.status_code == 400
    assert response.json()["detail"] == "query cannot be empty"


def test_search_rejects_missing_knowledge_base() -> None:
    response = client.get("/search?query=春天&knowledge_base_id=999")

    assert response.status_code == 404
    assert response.json()["detail"] == "knowledge base not found"
