"""Tests for AI-text detector using perplexity and burstiness."""

import pytest
from app.services.ai_detector import AIDetectorService


def test_ai_detector_too_short():
    detector = AIDetectorService(min_words=50)
    res = detector.analyze_text("This is a very short text.")
    assert res["overall_score"] == 0.0
    assert "insufficient" in res["status"].lower()


def test_ai_detector_mock_scoring(monkeypatch):
    detector = AIDetectorService(min_words=5)
    # Mock compute_perplexity to return deterministic values
    monkeypatch.setattr(detector, "_compute_block_score", lambda text: {"perplexity": 12.5, "burstiness": 0.3, "score": 65.0})

    res = detector.analyze_text(
        "Machine learning models have achieved remarkable success across diverse application domains.\n\n"
        "However, evaluating their inherent limitations remains critical for deployment."
    )
    assert res["overall_score"] == 65.0
    assert len(res["paragraphs"]) == 2
    assert "ai-likelihood" in res["disclaimer"].lower()
