"""Unit tests for plagiarism scoring service."""

import pytest

from app.services.plagiarism.fuzzy import ClassifiedMatch
from app.services.plagiarism.scoring import (
    ScoringParameters,
    ScoringService,
    SourceContribution,
)


class TestScoringService:
    """Test plagiarism scoring calculations."""

    def test_merge_overlapping_spans_no_overlap(self):
        """Test merging spans with no overlaps."""
        service = ScoringService()
        matches = [
            ClassifiedMatch(
                match_type="exact",
                submitted_start=0,
                submitted_end=10,
                source_start=0,
                source_end=10,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
            ClassifiedMatch(
                match_type="exact",
                submitted_start=20,
                submitted_end=30,
                source_start=20,
                source_end=30,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
        ]

        merged = service.merge_overlapping_spans(matches)

        assert len(merged) == 2
        assert merged[0] == (0, 10)
        assert merged[1] == (20, 30)

    def test_merge_overlapping_spans_with_overlap(self):
        """Test merging overlapping spans."""
        service = ScoringService()
        matches = [
            ClassifiedMatch(
                match_type="exact",
                submitted_start=0,
                submitted_end=15,
                source_start=0,
                source_end=15,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
            ClassifiedMatch(
                match_type="exact",
                submitted_start=10,
                submitted_end=20,
                source_start=10,
                source_end=20,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
        ]

        merged = service.merge_overlapping_spans(matches)

        # Should merge into one span from 0 to 20
        assert len(merged) == 1
        assert merged[0] == (0, 20)

    def test_merge_overlapping_spans_nested(self):
        """Test merging nested spans."""
        service = ScoringService()
        matches = [
            ClassifiedMatch(
                match_type="exact",
                submitted_start=0,
                submitted_end=30,
                source_start=0,
                source_end=30,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
            ClassifiedMatch(
                match_type="exact",
                submitted_start=10,
                submitted_end=20,
                source_start=10,
                source_end=20,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
        ]

        merged = service.merge_overlapping_spans(matches)

        # Nested span should be absorbed
        assert len(merged) == 1
        assert merged[0] == (0, 30)

    def test_merge_overlapping_spans_empty(self):
        """Test merging empty list."""
        service = ScoringService()
        merged = service.merge_overlapping_spans([])

        assert merged == []

    def test_calculate_source_contributions(self):
        """Test source contribution calculation."""
        service = ScoringService()

        # Create matches from two different sources
        matches = []
        for i in range(5):
            match = ClassifiedMatch(
                match_type="exact",
                submitted_start=i * 10,
                submitted_end=i * 10 + 5,
                source_start=0,
                source_end=5,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            )
            match.source_document_id = "doc1" if i < 3 else "doc2"
            match.source_title = "Document 1" if i < 3 else "Document 2"
            matches.append(match)

        contributions = service.calculate_source_contributions(matches, 100)

        assert len(contributions) == 2

        # Check that doc1 has more contribution (3 matches vs 2)
        assert contributions[0].matched_tokens == 15  # 3 matches * 5 tokens
        assert contributions[1].matched_tokens == 10  # 2 matches * 5 tokens

    def test_calculate_similarity_score_no_matches(self):
        """Test similarity score calculation with no matches."""
        service = ScoringService()
        parameters = ScoringParameters(
            k=5, w=4, min_match_tokens=8, exact_threshold=1.0,
            near_exact_threshold=0.85, excluded_sections=[]
        )

        score = service.calculate_similarity_score([], 1000, parameters)

        assert score.eligible_tokens == 1000
        assert score.matched_tokens == 0
        assert score.lexical_similarity_percent == 0.0
        assert score.largest_single_source_percent == 0.0

    def test_calculate_similarity_score_with_matches(self):
        """Test similarity score calculation with matches."""
        service = ScoringService()

        matches = [
            ClassifiedMatch(
                match_type="exact",
                submitted_start=0,
                submitted_end=50,
                source_start=0,
                source_end=50,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
        ]
        matches[0].source_document_id = "doc1"
        matches[0].source_title = "Document 1"

        parameters = ScoringParameters(
            k=5, w=4, min_match_tokens=8, exact_threshold=1.0,
            near_exact_threshold=0.85, excluded_sections=[]
        )

        score = service.calculate_similarity_score(matches, 1000, parameters)

        assert score.eligible_tokens == 1000
        assert score.matched_tokens == 50
        assert score.lexical_similarity_percent == 5.0  # 50/1000 * 100
        assert score.largest_single_source_percent == 5.0

    def test_calculate_similarity_score_overlap_not_double_counted(self):
        """Test that overlapping matches are not double-counted."""
        service = ScoringService()

        # Two overlapping matches
        matches = [
            ClassifiedMatch(
                match_type="exact",
                submitted_start=0,
                submitted_end=50,
                source_start=0,
                source_end=50,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
            ClassifiedMatch(
                match_type="exact",
                submitted_start=25,
                submitted_end=75,
                source_start=25,
                source_end=75,
                submitted_text="",
                source_text="",
                similarity_ratio=1.0,
                submitted_page=1,
                source_page=1,
            ),
        ]
        for match in matches:
            match.source_document_id = "doc1"
            match.source_title = "Document 1"

        parameters = ScoringParameters(
            k=5, w=4, min_match_tokens=8, exact_threshold=1.0,
            near_exact_threshold=0.85, excluded_sections=[]
        )

        score = service.calculate_similarity_score(matches, 1000, parameters)

        # Should be 75 tokens (0-75), not 100 (50+50)
        assert score.matched_tokens == 75
        assert score.lexical_similarity_percent == 7.5  # 75/1000 * 100

    def test_calculate_similarity_score_zero_tokens(self):
        """Test similarity score with zero eligible tokens."""
        service = ScoringService()
        parameters = ScoringParameters(
            k=5, w=4, min_match_tokens=8, exact_threshold=1.0,
            near_exact_threshold=0.85, excluded_sections=[]
        )

        score = service.calculate_similarity_score([], 0, parameters)

        assert score.eligible_tokens == 0
        assert score.matched_tokens == 0
        assert score.lexical_similarity_percent == 0.0
