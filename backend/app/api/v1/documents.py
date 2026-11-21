"""Document API endpoints for upload, retrieval, and deletion."""

import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import (
    AuthorizationError,
    FileProcessingError,
    NotFoundError,
    ValidationError,
)
from app.core.security import (
    compute_file_hash,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
    validate_pdf_content,
)
from app.db.session import get_db
from app.models.document import Document, DocumentChunk, DocumentPage
from app.schemas.document import (
    ChunkDetail,
    DeleteResponse,
    DocumentDetail,
    DocumentList,
    DocumentsResponse,
    DocumentUploadResponse,
    PageDetail,
)
from app.services.chunking import ChunkingService
from app.services.extraction import ExtractionService
from app.services.normalization import NormalizationService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def get_current_user_id() -> str:
    """Get current user ID.

    In Phase 1, we use a default user. In future phases, this will
    integrate with actual authentication.

    Returns:
        User ID string
    """
    return "default_user"


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Upload and process a document (PDF or TXT).

    Steps:
    1. Validate file (extension, size, MIME type)
    2. Save with random filename
    3. Extract text page-by-page
    4. Normalize text
    5. Chunk text
    6. Store in database
    7. Check for duplicates by hash
    """
    try:
        # Validate extension
        validate_file_extension(file.filename)

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate size
        validate_file_size(file_size)

        # Compute hash for deduplication
        from io import BytesIO
        file_hash = compute_file_hash(BytesIO(content))

        # Check if file already exists
        from sqlalchemy import select
        existing_doc = db.scalars(select(Document).where(Document.file_hash == file_hash)).first()
        if existing_doc:
            return DocumentUploadResponse(
                id=existing_doc.id,
                filename=existing_doc.filename,
                original_filename=existing_doc.original_filename,
                file_type=existing_doc.file_type,
                file_size_bytes=existing_doc.file_size_bytes,
                total_pages=existing_doc.total_pages,
                total_chars=existing_doc.total_chars,
                created_at=existing_doc.created_at,
                message="Document already exists (duplicate detected by hash)",
            )

        # Generate safe filename and save
        safe_filename = sanitize_filename(file.filename)
        file_path = settings.upload_dir / safe_filename

        file_path.write_bytes(content)

        # Validate MIME type
        validate_mime_type(file_path)

        # Additional PDF validation
        file_type = file_path.suffix.lower()[1:]  # Remove dot
        if file_type == "pdf":
            validate_pdf_content(file_path)

        # Extract text
        extraction_service = ExtractionService()
        extraction_result = extraction_service.extract(file_path)

        # Normalize text
        normalization_service = NormalizationService()
        normalized_pages = normalization_service.normalize_batch(
            [(page.text, page.page_number) for page in extraction_result.pages]
        )

        # Chunk text
        chunking_service = ChunkingService()
        chunks = chunking_service.chunk_pages(
            [(norm.text, norm.page_number) for norm in normalized_pages]
        )

        # Create document record
        doc_id = str(uuid.uuid4())
        document = Document(
            id=doc_id,
            filename=safe_filename,
            original_filename=file.filename,
            file_type=file_type,
            file_size_bytes=file_size,
            file_hash=file_hash,
            total_pages=extraction_result.total_pages,
            total_chars=extraction_result.total_chars,
            owner_id=user_id,
        )

        db.add(document)

        # Create page records
        for page, normalized in zip(extraction_result.pages, normalized_pages):
            doc_page = DocumentPage(
                document_id=doc_id,
                page_number=page.page_number,
                raw_text=page.text,
                normalized_text=normalized.text,
                char_count=len(normalized.text),
            )
            db.add(doc_page)

        # Create chunk records
        for chunk in chunks:
            doc_chunk = DocumentChunk(
                document_id=doc_id,
                chunk_index=chunk.chunk_id,
                page_number=chunk.page_number,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                text=chunk.text,
                token_count=chunk.token_count,
            )
            db.add(doc_chunk)

        db.commit()
        db.refresh(document)

        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_type=document.file_type,
            file_size_bytes=document.file_size_bytes,
            total_pages=document.total_pages,
            total_chars=document.total_chars,
            created_at=document.created_at,
        )

    except (ValidationError, FileProcessingError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        # Clean up file if something went wrong
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.get("", response_model=DocumentsResponse)
def list_documents(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all documents for the current user."""
    from sqlalchemy import select
    documents = db.scalars(
        select(Document)
        .where(Document.owner_id == user_id)
        .order_by(Document.created_at.desc())
    ).all()

    return DocumentsResponse(
        documents=[
            DocumentList(
                id=doc.id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                file_type=doc.file_type,
                file_size_bytes=doc.file_size_bytes,
                total_pages=doc.total_pages,
                created_at=doc.created_at,
            )
            for doc in documents
        ],
        total=len(documents),
    )


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get detailed information about a document."""
    from sqlalchemy import select
    document = db.scalars(select(Document).where(Document.id == document_id)).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Authorization check
    if document.owner_id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this document"
        )

    # Build response with previews
    pages = [
        PageDetail(
            page_number=page.page_number,
            char_count=page.char_count,
            text_preview=page.normalized_text[:200],
        )
        for page in document.pages
    ]

    chunks = [
        ChunkDetail(
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            char_start=chunk.char_start,
            char_end=chunk.char_end,
            token_count=chunk.token_count,
            text_preview=chunk.text[:100],
        )
        for chunk in document.chunks
    ]

    return DocumentDetail(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        total_pages=document.total_pages,
        total_chars=document.total_chars,
        owner_id=document.owner_id,
        created_at=document.created_at,
        pages=pages,
        chunks=chunks,
    )


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a document and all associated data.

    Removes:
    - Database records (document, pages, chunks)
    - Stored file
    """
    from sqlalchemy import select
    document = db.scalars(select(Document).where(Document.id == document_id)).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Authorization check
    if document.owner_id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this document"
        )

    # Get file path before deleting from DB
    file_path = settings.upload_dir / document.filename

    # Delete from database (cascades to pages and chunks)
    db.delete(document)
    db.commit()

    # Delete file
    if file_path.exists():
        file_path.unlink()

    return DeleteResponse(
        message="Document deleted successfully", deleted_id=document_id
    )
