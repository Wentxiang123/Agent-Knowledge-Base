"""Knowledge base CRUD service."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.services.vector_store_service import get_vector_store_service


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def create_knowledge_base(db: Session, payload: KnowledgeBaseCreate) -> models.KnowledgeBase:
    knowledge_base = models.KnowledgeBase(
        name=payload.name.strip(),
        description=_normalize_text(payload.description),
    )
    db.add(knowledge_base)
    db.commit()
    db.refresh(knowledge_base)
    return knowledge_base


def list_knowledge_bases(
    db: Session,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[models.KnowledgeBase], int]:
    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(models.KnowledgeBase)) or 0
    items = db.scalars(
        select(models.KnowledgeBase)
        .order_by(models.KnowledgeBase.created_at.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return list(items), total


def get_knowledge_base(db: Session, kb_id: int) -> models.KnowledgeBase:
    knowledge_base = db.get(models.KnowledgeBase, kb_id)
    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="knowledge base not found",
        )
    return knowledge_base


def update_knowledge_base(
    db: Session,
    kb_id: int,
    payload: KnowledgeBaseUpdate,
) -> models.KnowledgeBase:
    knowledge_base = get_knowledge_base(db, kb_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        knowledge_base.name = update_data["name"].strip()
    if "description" in update_data:
        knowledge_base.description = _normalize_text(update_data["description"])

    db.commit()
    db.refresh(knowledge_base)
    return knowledge_base


def delete_knowledge_base(db: Session, kb_id: int) -> None:
    knowledge_base = get_knowledge_base(db, kb_id)
    get_vector_store_service().delete_by_knowledge_base(kb_id)
    db.delete(knowledge_base)
    db.commit()
