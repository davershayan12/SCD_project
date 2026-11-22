"""Unit tests for Document Check debugging and root cause fixes."""

import pytest
from app.services.document_check import DocumentCheckOrchestrator


def test_search_failure_yields_inconclusive(monkeypatch):
    class FailingProvider:
        name = "failing"
        def search(self, query, max_results=5):
            raise RuntimeError("network down")

    monkeypatch.setattr("app.services.document_check.get_provider", lambda name, urls=None: FailingProvider())

    orchestrator = DocumentCheckOrchestrator(search_provider="failing")
    pages = [("This is a test document with enough words to trigger queries.", 1)]
    result = orchestrator.run_check("doc-err", "test.txt", pages)

    assert result.status == "inconclusive"
    assert "No matches found" in result.disclaimer
