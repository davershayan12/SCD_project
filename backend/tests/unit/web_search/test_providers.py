"""Tests for pluggable web search providers (no live network)."""

import pytest

from app.services.web_search.providers import (
    DdgsProvider,
    ScholarlyProvider,
    UrlListProvider,
    SearchHit,
    get_provider,
)


class FakeDDGS:
    """Stand-in for ddgs.DDGS that returns canned results."""

    def __init__(self, results=None, raise_exc=None):
        self._results = results or []
        self._raise = raise_exc

    def text(self, query, max_results=5):
        if self._raise:
            raise self._raise
        return self._results


def test_ddgs_provider_maps_results():
    provider = DdgsProvider(
        client_factory=lambda: FakeDDGS(
            results=[
                {"title": "Plagiarism detection", "href": "https://en.wikipedia.org/wiki/X", "body": "snippet one"},
                {"title": "No href here", "body": "skip me"},
            ]
        )
    )
    hits = provider.search("plagiarism", max_results=5)

    assert len(hits) == 1
    assert isinstance(hits[0], SearchHit)
    assert hits[0].url == "https://en.wikipedia.org/wiki/X"
    assert hits[0].provider == "ddgs"
    assert hits[0].snippet == "snippet one"


def test_ddgs_provider_swallows_errors():
    provider = DdgsProvider(client_factory=lambda: FakeDDGS(raise_exc=RuntimeError("rate limited")))
    assert provider.search("anything") == []


def test_ddgs_provider_dedupes_urls():
    provider = DdgsProvider(
        client_factory=lambda: FakeDDGS(
            results=[
                {"title": "A", "href": "https://example.com/a", "body": ""},
                {"title": "A again", "href": "https://example.com/a", "body": ""},
            ]
        )
    )
    hits = provider.search("q")
    assert len(hits) == 1


def test_url_list_provider():
    provider = UrlListProvider(["https://example.org/page"])
    hits = provider.search("ignored query")
    assert [h.url for h in hits] == ["https://example.org/page"]
    assert hits[0].provider == "urls"


def test_scholarly_provider_wraps_documents(monkeypatch):
    from app.services.connectors import scholarly

    class Doc:
        title = "A Paper"
        url = "https://arxiv.org/abs/1234.5678"
        text = "abstract text"
        repository = "arXiv"

    class FakeService:
        def search_scholarly_apis(self, query, limit=3):
            return [Doc()]

    provider = ScholarlyProvider(service=FakeService())
    hits = provider.search("deep learning", max_results=3)
    assert len(hits) == 1
    assert hits[0].provider == "scholarly"
    assert "A Paper" in hits[0].title


def test_get_provider_factory():
    assert isinstance(get_provider("ddgs"), DdgsProvider)
    assert isinstance(get_provider("scholarly"), ScholarlyProvider)
    assert isinstance(get_provider("urls", urls=["https://a.b"]), UrlListProvider)
    with pytest.raises(ValueError):
        get_provider("does-not-exist")
