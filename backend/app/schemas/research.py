"""Pydantic schemas for research gap analysis API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResearchAnalysisRequest(BaseModel):
    """Request to initiate cross-paper gap analysis."""

    document_ids: List[str] = Field(min_length=2, max_length=10, description="List of 2-10 paper document IDs")


class EvidenceSchema(BaseModel):
    page: int
    quote: str


class FieldWithEvidenceSchema(BaseModel):
    value: str
    evidence: List[EvidenceSchema] = Field(default_factory=list)


class PaperProfileResponse(BaseModel):
    paper_id: str
    title: str
    year: int
    research_problem: FieldWithEvidenceSchema
    objectives: List[FieldWithEvidenceSchema]
    methodology: List[FieldWithEvidenceSchema]
    explicit_limitations: List[FieldWithEvidenceSchema]
    author_future_work: List[FieldWithEvidenceSchema]


class GapItemResponse(BaseModel):
    category: str
    source_label: str  # Author-reported, System-observed pattern, AI-suggested direction
    description: str
    supporting_paper_ids: List[str]
    evidence: List[Dict[str, Any]]
    why_it_matters: str
    suggested_research_question: str
    confidence: str
    confidence_reason: str
    scope_warning: str


class ResearchReportResponse(BaseModel):
    report_id: str
    status: str
    papers_analyzed: int
    profiles: List[Dict[str, Any]]
    gaps: List[GapItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True
