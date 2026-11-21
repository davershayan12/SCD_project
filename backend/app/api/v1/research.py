"""Research analysis API endpoints."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.schemas.research import (
    ResearchAnalysisRequest,
    ResearchReportResponse,
    GapItemResponse,
)
from app.services.research.profile import ProfileExtractionService
from app.services.research.gaps import GapGeneratorService

router = APIRouter(prefix="/api/v1/research-analysis", tags=["research-analysis"])


def get_current_user_id() -> str:
    return "default_user"


@router.post("/jobs", response_model=ResearchReportResponse, status_code=201)
async def create_research_analysis_job(
    request: ResearchAnalysisRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Initiate cross-paper gap analysis on 2-10 documents."""
    if len(request.document_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 papers for comparison")

    # Fetch documents
    documents = db.scalars(
        select(Document).where(Document.id.in_(request.document_ids), Document.owner_id == user_id)
    ).all()

    if len(documents) != len(request.document_ids):
        raise HTTPException(status_code=404, detail="One or more documents not found or unauthorized")

    extractor = ProfileExtractionService()
    gap_generator = GapGeneratorService()

    profiles = []
    for doc in documents:
        pages = [(p.normalized_text, p.page_number) for p in doc.pages]
        try:
            profile_res = extractor.extract_profile(doc.id, pages, title_hint=doc.original_filename)
            profiles.append(profile_res)
        except Exception as e:
            # Mark paper profile as failed
            profiles.append({
                "paper_id": doc.id,
                "profile": {"title": doc.original_filename, "research_problem": {"value": f"Extraction failed: {str(e)}", "evidence": []}},
                "status": "failed",
            })

    # Generate gaps across successful profiles
    valid_profiles = [p for p in profiles if p.get("status") != "failed"]
    gaps = gap_generator.generate_gaps(valid_profiles)

    report_id = str(uuid.uuid4())

    formatted_gaps = [
        GapItemResponse(
            category=g["category"],
            source_label=g["source_label"],
            description=g["description"],
            supporting_paper_ids=g["supporting_paper_ids"],
            evidence=g["evidence"],
            why_it_matters=g["why_it_matters"],
            suggested_research_question=g["suggested_research_question"],
            confidence=g["confidence"],
            confidence_reason=g["confidence_reason"],
            scope_warning=g["scope_warning"],
        )
        for g in gaps
    ]

    return ResearchReportResponse(
        report_id=report_id,
        status="completed",
        papers_analyzed=len(documents),
        profiles=profiles,
        gaps=formatted_gaps,
        created_at=datetime.utcnow(),
    )
