"""Unit tests for research gap extraction and evidence verification."""

import pytest

from app.services.research.evidence import EvidenceVerificationService
from app.services.research.sections import SectionDetectionService
from app.services.ollama import OllamaService
from app.services.research.profile import ProfileExtractionService


class TestSectionDetection:
    """Test academic section detection."""

    def test_detect_sections(self):
        """Test detecting sections from page text."""
        service = SectionDetectionService()
        pages = [
            ("Abstract\nThis paper presents a new method...", 1),
            ("1. Introduction\nBackground and motivation...", 1),
            ("2. Methodology\nWe propose an approach...", 2),
            ("3. Experiments\nResults show improvement...", 3),
            ("References\n[1] Smith et al.", 4),
        ]

        sections = service.detect_sections(pages)
        assert len(sections) > 0


class TestEvidenceVerification:
    """Test deterministic evidence verification."""

    def test_verify_exact_quote(self):
        """Test verifying an exact quote on the correct page."""
        service = EvidenceVerificationService(fuzzy_threshold=0.8)
        pages = [
            ("In this paper, we propose a novel transformer model for NLP.", 1),
            ("The results demonstrate state-of-the-art performance.", 2),
        ]

        result = service.verify_quote(
            quote="propose a novel transformer model",
            claimed_page=1,
            document_pages=pages,
        )

        assert result.is_verified is True
        assert result.similarity_ratio >= 0.8

    def test_verify_unsupported_quote(self):
        """Test rejecting a fabricated or incorrect quote."""
        service = EvidenceVerificationService(fuzzy_threshold=0.85)
        pages = [
            ("This is page one text about deep learning.", 1),
        ]

        result = service.verify_quote(
            quote="completely fabricated quote about quantum physics",
            claimed_page=1,
            document_pages=pages,
        )

        assert result.is_verified is False
