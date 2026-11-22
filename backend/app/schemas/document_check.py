"""Pydantic schemas for Document Check API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentCheckRequest(BaseModel):
    """Request to run document check (web plagiarism + AI detection)."""

    document_id: str = Field(description="Uploaded document ID")
    search_provider: Optional[str] = Field(default="ddgs", description="Search provider: ddgs, scholarly, urls, none")
    custom_urls: Optional[List[str]] = Field(default=None, description="Optional custom URLs to check against")


class DocumentCheckResponse(BaseModel):
    """Response containing complete check results."""

    document_id: str
    filename: str
    status: str
    corpus_scope: str
    eligible_word_count: int
    matched_word_count: int
    lexical_similarity_percent: float
    largest_single_source_percent: float
    matches: List[Dict[str, Any]]
    ai_detection: Dict[str, Any]
    status_diagnostics: Dict[str, Any]
    disclaimer: str
    created_at: str
