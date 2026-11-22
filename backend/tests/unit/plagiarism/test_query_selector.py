"""Tests for distinctive query selection."""

import pytest
from app.services.plagiarism.query_selector import QuerySelector


def test_query_selector_extraction():
    selector = QuerySelector(phrase_words=8)
    text = "This is a very unique sentence about machine learning algorithms in modern natural language processing."
    queries = selector.select_queries(text, max_queries=2)
    assert len(queries) > 0
    assert len(queries[0].split()) >= 6
