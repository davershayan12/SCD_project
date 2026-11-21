"""Database models for plagiarism reports."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.document import Base


class PlagiarismReport(Base):
    """Plagiarism analysis report."""

    __tablename__ = "plagiarism_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    corpus_scope: Mapped[str] = mapped_column(String(100), nullable=False)
    eligible_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    matched_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lexical_similarity_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    largest_single_source_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="plagiarism_reports")
    matches: Mapped[List["PlagiarismMatch"]] = relationship(
        "PlagiarismMatch", back_populates="report", cascade="all, delete-orphan"
    )


class PlagiarismMatch(Base):
    """Individual match between documents."""

    __tablename__ = "plagiarism_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("plagiarism_reports.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_document_id: Mapped[str] = mapped_column(String(36), nullable=False)

    match_type: Mapped[str] = mapped_column(String(20), nullable=False)  # exact, near-exact
    submitted_page: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_start: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_end: Mapped[int] = mapped_column(Integer, nullable=False)
    source_page: Mapped[int] = mapped_column(Integer, nullable=False)
    source_start: Mapped[int] = mapped_column(Integer, nullable=False)
    source_end: Mapped[int] = mapped_column(Integer, nullable=False)
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    submitted_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    report: Mapped["PlagiarismReport"] = relationship("PlagiarismReport", back_populates="matches")


# Add relationship to Document model
from app.models.document import Document  # noqa: E402

Document.plagiarism_reports = relationship(
    "PlagiarismReport", back_populates="document", cascade="all, delete-orphan"
)