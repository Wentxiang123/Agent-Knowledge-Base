import os
import shutil
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./data/test_app.db"
os.environ["UPLOAD_DIR"] = "./data/test_uploads"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.services.document_service import chunk_text

client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module() -> None:
    test_db = Path("./data/test_app.db")
    if test_db.exists():
        test_db.unlink()
    shutil.rmtree("./data/test_uploads", ignore_errors=True)


def create_test_knowledge_base() -> int:
    response = client.post(
        "/knowledge-bases",
        json={"name": "文学作品", "description": "测试文档上传"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_chunk_text_uses_overlap() -> None:
    text = "0123456789" * 70
    chunks = chunk_text(text, chunk_size=100, overlap=10)

    assert len(chunks) > 1
    assert chunks[0][-10:] == chunks[1][:10]


def test_upload_text_document_creates_chunks() -> None:
    kb_id = create_test_knowledge_base()
    content = "春天来了，万物复苏。" * 120

    response = client.post(
        f"/knowledge-bases/{kb_id}/documents/text",
        json={"title": "春", "content": content},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document"]["title"] == "春"
    assert data["document"]["kb_id"] == kb_id
    assert data["chunk_count"] > 1
    assert data["chunks"][0]["chunk_index"] == 0


def test_upload_gb18030_txt_document() -> None:
    kb_id = create_test_knowledge_base()
    raw_content = "少年闰土在海边看瓜。".encode("gb18030")

    response = client.post(
        f"/knowledge-bases/{kb_id}/documents/file",
        data={"title": "故乡"},
        files={"file": ("guxiang.txt", raw_content, "text/plain")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document"]["title"] == "故乡"
    assert data["chunk_count"] == 1
    assert "少年闰土" in data["chunks"][0]["content"]


def test_upload_rejects_non_txt_file() -> None:
    kb_id = create_test_knowledge_base()

    response = client.post(
        f"/knowledge-bases/{kb_id}/documents/file",
        files={"file": ("notes.md", b"hello", "text/markdown")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "only .txt files are supported"
