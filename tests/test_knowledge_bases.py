import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./data/test_app.db"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module() -> None:
    test_db = Path("./data/test_app.db")
    if test_db.exists():
        test_db.unlink()


def test_create_list_get_update_and_delete_knowledge_base() -> None:
    create_response = client.post(
        "/knowledge-bases",
        json={"name": "文学作品", "description": "用于测试语义搜索的知识库"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == 1
    assert created["name"] == "文学作品"

    list_response = client.get("/knowledge-bases?page=1&page_size=10")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["total"] == 1
    assert listed["items"][0]["name"] == "文学作品"

    get_response = client.get("/knowledge-bases/1")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "用于测试语义搜索的知识库"

    update_response = client.put(
        "/knowledge-bases/1",
        json={"name": "现代文学", "description": "更新后的描述"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "现代文学"

    delete_response = client.delete("/knowledge-bases/1")
    assert delete_response.status_code == 204

    missing_response = client.get("/knowledge-bases/1")
    assert missing_response.status_code == 404
