"""Document ingestion and text chunking service."""

import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.schemas import DocumentTextCreate
from app.services import kb_service

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
TXT_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    text = _normalize_text(text)
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document content cannot be empty",
        )
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be greater than or equal to 0 and smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = end - overlap

    return chunks


def decode_txt_content(filename: str, raw_content: bytes) -> str:
    if not filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only .txt files are supported",
        )
    if not raw_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploaded file cannot be empty",
        )

    for encoding in TXT_ENCODINGS:
        try:
            return raw_content.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="failed to decode txt file; please use UTF-8 or GB18030 encoding",
    )


def save_uploaded_file(kb_id: int, filename: str, raw_content: bytes) -> Path:
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./data/uploads")) / str(kb_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name or "document.txt"
    target = upload_dir / f"{uuid4().hex}_{safe_name}"
    target.write_bytes(raw_content)
    return target


def create_document_from_text(
    db: Session,
    kb_id: int,
    payload: DocumentTextCreate,
) -> tuple[models.Document, list[models.Chunk]]:
    kb_service.get_knowledge_base(db, kb_id)

    title = _normalize_text(payload.title)
    content = _normalize_text(payload.content)
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document title cannot be empty",
        )

    chunks_content = chunk_text(content)
    document = models.Document(kb_id=kb_id, title=title, content=content)
    db.add(document)
    db.flush()

    chunks = [
        models.Chunk(
            kb_id=kb_id,
            document_id=document.id,
            content=chunk,
            chunk_index=index,
        )
        for index, chunk in enumerate(chunks_content)
    ]
    db.add_all(chunks)
    db.commit()
    db.refresh(document)
    for chunk in chunks:
        db.refresh(chunk)
    return document, chunks


def create_document_from_txt_file(
    db: Session,
    kb_id: int,
    filename: str,
    raw_content: bytes,
    title: str | None = None,
) -> tuple[models.Document, list[models.Chunk]]:
    kb_service.get_knowledge_base(db, kb_id)
    content = decode_txt_content(filename, raw_content)
    save_uploaded_file(kb_id, filename, raw_content)
    document_title = _normalize_text(title) or Path(filename).stem or "Untitled Document"
    payload = DocumentTextCreate(title=document_title, content=content)
    return create_document_from_text(db, kb_id, payload)
