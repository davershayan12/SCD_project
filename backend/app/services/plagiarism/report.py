"""Plagiarism report generation service."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.services.plagiarism.fuzzy import ClassifiedMatch
from app.services.plagiarism.scoring import ScoringParameters, SimilarityScore


@dataclass
class MatchDetail:
    """Detail of a single match for the report."""

    match_type: str
    submitted_page: int
    submitted_span: List[int]  # [start, end]
    source_document_id: str
    source_title: str
    source_page: int
    similarity: float
    submitted_text: str
    source_text: str


@dataclass
class PlagiarismReport:
    """Complete plagiarism report."""

    report_id: str
    document_id: str
    status: str  # "completed", "failed"
    corpus_scope: str  # e.g., "user documents (12 docs)"
    parameters: dict  # JSON-serializable parameters
    eligible_word_count: int
    matched_word_count: int
    lexical_similarity_percent: float
    largest_single_source_percent: float
    matches: List[MatchDetail]
    disclaimer: str
    created_at: datetime


class ReportService:
    """Service for generating plagiarism reports."""

    def __init__(self):
        """Initialize report service."""
        self.disclaimer = (
            "Similarity is not a determination of plagiarism. "
            "This report compares the submitted document against your uploaded corpus. "
            "Matches may include quotes, references, common phrases, or valid paraphrases. "
            "Review each match to determine if attribution is appropriate."
        )

    def generate_report(
        self,
        document_id: str,
        matches: List[ClassifiedMatch],
        similarity_score: SimilarityScore,
        corpus_documents: List[dict],
        include_references: bool = True,
    ) -> PlagiarismReport:
        """Generate a complete plagiarism report.

        Args:
            document_id: ID of the submitted document
            matches: List of all classified matches
            similarity_score: Calculated similarity score
            corpus_documents: List of corpus document info (id, title)
            include_references: Whether references are included in the check

        Returns:
            Complete PlagiarismReport
        """
        # Build corpus scope string
        corpus_scope = f"user documents ({len(corpus_documents)} doc{'s' if len(corpus_documents) != 1 else ''})"

        # Convert matches to report format
        match_details = []
        source_titles = {doc["id"]: doc.get("title", doc["id"]) for doc in corpus_documents}

        for match in matches:
            match_details.append(
                MatchDetail(
                    match_type=match.match_type,
                    submitted_page=match.submitted_page,
                    submitted_span=[match.submitted_start, match.submitted_end],
                    source_document_id=match.source_document_id,
                    source_title=source_titles.get(match.source_document_id, "Unknown"),
                    source_page=match.source_page,
                    similarity=match.similarity_ratio,
                    submitted_text=match.submitted_text,
                    source_text=match.source_text,
                )
            )

        # Sort matches by position in submitted document
        match_details.sort(key=lambda m: m.submitted_span[0])

        return PlagiarismReport(
            report_id=str(uuid.uuid4()),
            document_id=document_id,
            status="completed",
            corpus_scope=corpus_scope,
            parameters={
                "k": similarity_score.parameters.k,
                "w": similarity_score.parameters.w,
                "min_tokens": similarity_score.parameters.min_match_tokens,
                "excluded": [] if include_references else ["references"],
            },
            eligible_word_count=similarity_score.eligible_tokens,
            matched_word_count=similarity_score.matched_tokens,
            lexical_similarity_percent=similarity_score.lexical_similarity_percent,
            largest_single_source_percent=similarity_score.largest_single_source_percent,
            matches=match_details,
            disclaimer=self.disclaimer,
            created_at=datetime.utcnow(),
        )

    def to_dict(self, report: PlagiarismReport) -> dict:
        """Convert report to dictionary for JSON serialization.

        Args:
            report: PlagiarismReport to convert

        Returns:
            JSON-serializable dictionary
        """
        return {
            "report_id": report.report_id,
            "document_id": report.document_id,
            "status": report.status,
            "corpus_scope": report.corpus_scope,
            "parameters": report.parameters,
            "eligible_word_count": report.eligible_word_count,
            "matched_word_count": report.matched_word_count,
            "lexical_similarity_percent": report.lexical_similarity_percent,
            "largest_single_source_percent": report.largest_single_source_percent,
            "matches": [
                {
                    "match_type": m.match_type,
                    "submitted_page": m.submitted_page,
                    "submitted_span": m.submitted_span,
                    "source_document_id": m.source_document_id,
                    "source_title": m.source_title,
                    "source_page": m.source_page,
                    "similarity": m.similarity,
                    "submitted_text": m.submitted_text[:500],  # Truncate for display
                    "source_text": m.source_text[:500],
                }
                for m in report.matches
            ],
            "disclaimer": report.disclaimer,
            "created_at": report.created_at.isoformat(),
        }