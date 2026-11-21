"""Pydantic schemas for document operations."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""

    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    total_pages: int
    total_chars: int
    created_at: datetime
    message: str = "Document uploaded and processed successfully"

    class Config:
        from_attributes = True


class PageDetail(BaseModel):
    """Detail of a single page."""

    page_number: int
    char_count: int
    text_preview: str = Field(description="First 200 characters")


class ChunkDetail(BaseModel):
    """Detail of a single chunk."""

    chunk_index: int
    page_number: int
    char_start: int
    char_end: int
    token_count: int
    text_preview: str = Field(description="First 100 characters")


class DocumentDetail(BaseModel):
    """Detailed document information."""

    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    total_pages: int
    total_chars: int
    owner_id: str
    created_at: datetime
    pages: List[PageDetail]
    chunks: List[ChunkDetail]

    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """List of documents (summary)."""

    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    total_pages: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentsResponse(BaseModel):
    """Response for listing documents."""

    documents: List[DocumentList]
    total: int


class DeleteResponse(BaseModel):
    """Response for document deletion."""

    message: str
    deleted_id: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
