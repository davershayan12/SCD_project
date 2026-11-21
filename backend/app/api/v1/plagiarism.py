"""Plagiarism detection API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.document import Document
from app.models.plagiarism import PlagiarismReport as DBReport
from app.schemas.plagiarism import (
    ErrorResponse,
    PlagiarismCheckRequest,
    PlagiarismCheckResponse,
    PlagiarismReportResponse,
    MatchDetailSchema,
)
from app.services.plagiarism.detection import PlagiarismDetectionService

router = APIRouter(prefix="/api/v1/plagiarism", tags=["plagiarism"])


def get_current_user_id() -> str:
    """Get current user ID.

    In Phase 2, we use a default user. In future phases, this will
    integrate with actual authentication.

    Returns:
        User ID string
    """
    return "default_user"


@router.post("/check", response_model=PlagiarismCheckResponse, status_code=202)
async def check_document_plagiarism(
    request: PlagiarismCheckRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Check a document for plagiarism.

    Compares the document against the user's corpus of uploaded documents.

    Args:
        request: Plagiarism check request
        db: Database session
        user_id: Current user ID

    Returns:
        PlagiarismCheckResponse with report ID
    """
    try:
        # Verify document exists and user owns it
        document = db.scalars(
            select(Document).where(Document.id == request.document_id)
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to check this document")

        # Initialize detection service
        detection_service = PlagiarismDetectionService()

        # Run plagiarism check
        report_id = detection_service.check_document(
            document_id=request.document_id,
            db=db,
            user_id=user_id,
            compare_with=request.compare_with,
            include_references=request.include_references,
        )

        return PlagiarismCheckResponse(
            report_id=report_id,
            status="completed",
            message="Plagiarism check completed successfully",
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Plagiarism check failed: {str(e)}",
        )


@router.get("/reports/{report_id}", response_model=PlagiarismReportResponse)
def get_plagiarism_report(
    report_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get a plagiarism report by ID.

    Args:
        report_id: Report ID
        db: Database session
        user_id: Current user ID

    Returns:
        Complete plagiarism report
    """
    # Get report
    report = db.scalars(
        select(DBReport).where(DBReport.id == report_id)
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check authorization (document ownership)
    document = db.scalars(
        select(Document).where(Document.id == report.document_id)
    ).first()

    if not document or document.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this report")

    # Build response
    import json

    matches = [
        MatchDetailSchema(
            match_type=match.match_type,
            submitted_page=match.submitted_page,
            submitted_span=[match.submitted_start, match.submitted_end],
            source_document_id=match.source_document_id,
            source_title=get_document_title(match.source_document_id, db),
            source_page=match.source_page,
            similarity=match.similarity,
            submitted_text=match.submitted_text,
            source_text=match.source_text,
        )
        for match in report.matches
    ]

    return PlagiarismReportResponse(
        report_id=report.id,
        document_id=report.document_id,
        status=report.status,
        corpus_scope=report.corpus_scope,
        parameters=json.loads(report.parameters_json),
        eligible_word_count=report.eligible_word_count,
        matched_word_count=report.matched_word_count,
        lexical_similarity_percent=report.lexical_similarity_percent,
        largest_single_source_percent=report.largest_single_source_percent,
        matches=matches,
        disclaimer=report.disclaimer,
        created_at=report.created_at,
    )


@router.get("/reports")
def list_plagiarism_reports(
    document_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List plagiarism reports for the current user.

    Args:
        document_id: Optional filter by document ID
        db: Database session
        user_id: Current user ID

    Returns:
        List of reports
    """
    query = select(DBReport)

    if document_id:
        query = query.where(DBReport.document_id == document_id)

    # Filter by user ownership via document
    query = query.join(Document).where(Document.owner_id == user_id)

    reports = db.scalars(query.order_by(DBReport.created_at.desc())).all()

    return {
        "reports": [
            {
                "report_id": r.id,
                "document_id": r.document_id,
                "status": r.status,
                "lexical_similarity_percent": r.lexical_similarity_percent,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ],
        "total": len(reports),
    }


@router.delete("/reports/{report_id}")
def delete_plagiarism_report(
    report_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a plagiarism report.

    Args:
        report_id: Report ID to delete
        db: Database session
        user_id: Current user ID

    Returns:
        Success message
    """
    report = db.scalars(
        select(DBReport).where(DBReport.id == report_id)
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check authorization
    document = db.scalars(
        select(Document).where(Document.id == report.document_id)
    ).first()

    if not document or document.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this report")

    db.delete(report)
    db.commit()

    return {"message": "Report deleted successfully", "report_id": report_id}


def get_document_title(document_id: str, db: Session) -> str:
    """Helper to get document title."""
    doc = db.scalars(
        select(Document).where(Document.id == document_id)
    ).first()
    return doc.original_filename if doc else "Unknown"
