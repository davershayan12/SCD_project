"""Unit tests for cross-paper comparison and gap generation."""

import pytest

from app.services.research.comparator import CrossPaperComparator
from app.services.research.gaps import GapGeneratorService


class TestCrossPaperComparator:
    """Test comparator service."""

    def test_compare_profiles_empty(self):
        comparator = CrossPaperComparator()
        result = comparator.compare_profiles([])
        assert result["papers_count"] == 0

    def test_compare_profiles_with_data(self):
        comparator = CrossPaperComparator()
        profiles = [
            {
                "paper_id": "doc1",
                "profile": {
                    "datasets": [{"value": "ImageNet"}],
                    "explicit_limitations": [{"value": "High latency"}],
                },
            },
            {
                "paper_id": "doc2",
                "profile": {
                    "datasets": [{"value": "ImageNet"}],
                    "explicit_limitations": [{"value": "High latency"}],
                },
            },
        ]

        result = comparator.compare_profiles(profiles)
        assert result["papers_count"] == 2
        assert "imagenet" in result["shared_datasets"]
        assert "high latency" in result["repeated_limitations"]


class TestGapGeneratorService:
    """Test gap generator service."""

    def test_generate_gaps(self):
        generator = GapGeneratorService()
        profiles = [
            {
                "paper_id": "doc1",
                "profile": {
                    "explicit_limitations": [{"value": "Scalability issues", "evidence": [{"page": 1, "quote": "Scalability issues."}]}],
                    "author_future_work": [{"value": "Explore distributed training", "evidence": [{"page": 5, "quote": "Explore distributed training."}]}],
                },
            },
            {
                "paper_id": "doc2",
                "profile": {
                    "explicit_limitations": [{"value": "Scalability issues", "evidence": [{"page": 2, "quote": "Scalability issues."}]}],
                    "author_future_work": [{"value": "Optimize memory", "evidence": [{"page": 6, "quote": "Optimize memory."}]}],
                },
            },
        ]

        gaps = generator.generate_gaps(profiles)
        assert len(gaps) > 0
        # Check source labels and scope warning present
        for gap in gaps:
            assert "source_label" in gap
            assert "scope_warning" in gap
            assert gap["scope_warning"] == GapGeneratorService.SCOPE_WARNING
