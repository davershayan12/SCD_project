"""Unit tests for Document Check orchestrator with mocked search and fetch."""

import pytest
from app.services.document_check import DocumentCheckOrchestrator
from app.services.web_search.providers import SearchHit


class FakeProvider:
    name = "fake"
    def search(self, query, max_results=5):
        return [SearchHit(url="https://example.com/test", title="Test Page", snippet="test snippet")]


class FakeFetcher:
    def fetch_url(self, url):
        class Res:
            status_code = 200
            content_type = "text/html"
            text = "This is a test document with matching content from the web."
        return Res()


def test_document_check_orchestration(monkeypatch):
    # Mock provider and fetcher
    monkeypatch.setattr("app.services.document_check.get_provider", lambda name, urls=None: FakeProvider())

    orchestrator = DocumentCheckOrchestrator(search_provider="fake")
    orchestrator.fetcher = FakeFetcher()

    pages = [("This is a test document with matching content from the web.", 1)]
    result = orchestrator.run_check("doc-1", "test.txt", pages)

    assert result.document_id == "doc-1"
    assert result.status == "completed"
    assert "ai_detection" in result.__dict__
    assert "status_diagnostics" in result.__dict__
    assert result.status_diagnostics["queries_run"] >= 0
