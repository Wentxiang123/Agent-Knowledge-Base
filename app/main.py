from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.schemas import (
    DocumentIngestResponse,
    DocumentTextCreate,
    KnowledgeBaseCreate,
    KnowledgeBaseList,
    KnowledgeBaseRead,
    KnowledgeBaseUpdate,
)
from app.services import document_service, kb_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Agent Knowledge Base",
    description="Semantic knowledge base API with streaming search and MCP integration.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/knowledge-bases",
    response_model=KnowledgeBaseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
) -> models.KnowledgeBase:
    return kb_service.create_knowledge_base(db, payload)


@app.get("/knowledge-bases", response_model=KnowledgeBaseList)
def list_knowledge_bases(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> KnowledgeBaseList:
    items, total = kb_service.list_knowledge_bases(db, page=page, page_size=page_size)
    return KnowledgeBaseList(items=items, total=total, page=page, page_size=page_size)


@app.get("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseRead)
def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
) -> models.KnowledgeBase:
    return kb_service.get_knowledge_base(db, kb_id)


@app.put("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseRead)
def update_knowledge_base(
    kb_id: int,
    payload: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
) -> models.KnowledgeBase:
    return kb_service.update_knowledge_base(db, kb_id, payload)


@app.delete("/knowledge-bases/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
) -> Response:
    kb_service.delete_knowledge_base(db, kb_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/knowledge-bases/{kb_id}/documents/text",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_text_document(
    kb_id: int,
    payload: DocumentTextCreate,
    db: Session = Depends(get_db),
) -> DocumentIngestResponse:
    document, chunks = document_service.create_document_from_text(db, kb_id, payload)
    return DocumentIngestResponse(document=document, chunks=chunks, chunk_count=len(chunks))


@app.post(
    "/knowledge-bases/{kb_id}/documents/file",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_txt_document(
    kb_id: int,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> DocumentIngestResponse:
    raw_content = await file.read()
    document, chunks = document_service.create_document_from_txt_file(
        db=db,
        kb_id=kb_id,
        filename=file.filename or "document.txt",
        raw_content=raw_content,
        title=title,
    )
    return DocumentIngestResponse(document=document, chunks=chunks, chunk_count=len(chunks))
