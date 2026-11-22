"""Pydantic schemas for plagiarism detection API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Request Schemas
class PlagiarismCheckRequest(BaseModel):
    """Request to check a document for plagiarism."""

    document_id: str = Field(description="ID of the uploaded document to check")
    compare_with: Optional[List[str]] = Field(
        default=None,
        description="Specific document IDs to compare against (default: all user documents)",
    )
    include_references: bool = Field(
        default=True,
        description="Whether to include references section in the check",
    )
    online_mode: bool = Field(
        default=False,
        description="Explicit privacy opt-in to check online open-access scholarly APIs",
    )
    custom_urls: Optional[List[str]] = Field(
        default=None,
        description="Optional list of custom URLs to check against",
    )


class PlagiarismCheckTextRequest(BaseModel):
    """Request to check pasted text for plagiarism."""

    text: str = Field(min_length=10, description="Text content to check")
    source_title: str = Field(default="Pasted Text", description="Title for the pasted text")
    compare_with: Optional[List[str]] = Field(
        default=None,
        description="Document IDs to compare against",
    )


# Response Schemas
class MatchDetailSchema(BaseModel):
    """Detail of a single match."""

    match_type: str
    submitted_page: int
    submitted_span: List[int]
    source_document_id: str
    source_title: str
    source_page: int
    similarity: float
    submitted_text: str
    source_text: str

    class Config:
        from_attributes = True


class PlagiarismReportResponse(BaseModel):
    """Plagiarism report response."""

    report_id: str
    document_id: str
    status: str
    corpus_scope: str
    parameters: dict
    eligible_word_count: int
    matched_word_count: int
    lexical_similarity_percent: float
    largest_single_source_percent: float
    matches: List[MatchDetailSchema]
    disclaimer: str
    created_at: datetime

    class Config:
        from_attributes = True


class PlagiarismCheckResponse(BaseModel):
    """Response for plagiarism check initiation."""

    report_id: str
    status: str
    message: str


class PlagiarismJobStatus(BaseModel):
    """Status of a plagiarism check job."""

    report_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = None
    message: Optional[str] = None
    result: Optional[PlagiarismReportResponse] = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None