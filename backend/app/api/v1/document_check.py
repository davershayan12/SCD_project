"""Document Check API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.schemas.document_check import DocumentCheckRequest, DocumentCheckResponse
from app.services.document_check import DocumentCheckOrchestrator

router = APIRouter(prefix="/api/v1/document-check", tags=["document-check"])


def get_current_user_id() -> str:
    return "default_user"


@router.post("", response_model=DocumentCheckResponse)
async def run_document_check(
    request: DocumentCheckRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Run combined web plagiarism search and AI-text likelihood detection."""
    doc = db.scalars(
        select(Document).where(Document.id == request.document_id, Document.owner_id == user_id)
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = [(p.normalized_text, p.page_number) for p in doc.pages]
    if not pages:
        raise HTTPException(status_code=400, detail="Document contains no extracted text")

    try:
        orchestrator = DocumentCheckOrchestrator(
            search_provider=request.search_provider,
            custom_urls=request.custom_urls,
        )
        result = orchestrator.run_check(
            document_id=doc.id,
            filename=doc.original_filename,
            pages=pages,
        )
        return DocumentCheckResponse(**result.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document check failed: {str(e)}")
