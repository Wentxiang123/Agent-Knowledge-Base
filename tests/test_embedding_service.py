from app.services.embedding_service import DEFAULT_LOCAL_EMBEDDING_DIMENSION, EmbeddingService


def test_local_embedding_is_deterministic() -> None:
    service = EmbeddingService()
    first = service.embed_text("春天来了")
    second = service.embed_text("春天来了")

    assert first == second
    assert len(first) == DEFAULT_LOCAL_EMBEDDING_DIMENSION
    assert any(value != 0 for value in first)


def test_local_embedding_changes_with_text() -> None:
    service = EmbeddingService()
    spring = service.embed_text("春天来了")
    hometown = service.embed_text("少年闰土")

    assert spring != hometown
