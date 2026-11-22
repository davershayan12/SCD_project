"""Pluggable web search providers for the Document Check feature.

Providers are deliberately dumb: they return URLs and snippets. Fetching,
extraction, matching and scoring happen downstream so every provider is
treated identically and a provider failure can never masquerade as a
"no match" result.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Protocol

logger = logging.getLogger(__name__)

DEMO_PROVIDER_WARNING = (
    "Demo search provider: results may be rate-limited, incomplete or blocked. "
    "For a guaranteed demo use the URL list."
)


@dataclass
class SearchHit:
    """One search result pointing at a page to fetch and compare."""

    url: str
    title: str = ""
    snippet: str = ""
    provider: str = ""


class SearchProvider(Protocol):
    """Interface every search provider implements."""

    name: str

    def search(self, query: str, max_results: int = 5) -> List[SearchHit]:
        """Return candidate pages for a query."""


@dataclass
class DdgsProvider:
    """Demo web search via the MIT-licensed `ddgs` package.

    This is the only provider that searches the general web without a key.
    It is explicitly a demo fallback: upstream engines rate-limit and
    occasionally return nothing.
    """

    name: str = "ddgs"
    client_factory: Optional[Callable[[], object]] = None

    def _client(self):
        if self.client_factory is not None:
            return self.client_factory()
        from ddgs import DDGS  # imported lazily so tests need no network

        return DDGS()

    def search(self, query: str, max_results: int = 5) -> List[SearchHit]:
        try:
            raw = list(self._client().text(query, max_results=max_results))
        except Exception as exc:  # rate limits, no results, network errors
            logger.info("ddgs search failed for query: %s", exc)
            return []

        hits: List[SearchHit] = []
        seen: set[str] = set()
        for item in raw:
            url = (item.get("href") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            hits.append(
                SearchHit(
                    url=url,
                    title=(item.get("title") or "").strip(),
                    snippet=(item.get("body") or "").strip(),
                    provider=self.name,
                )
            )
        return hits


@dataclass
class ScholarlyProvider:
    """Free scholarly APIs (arXiv / OpenAlex) through the existing connector."""

    name: str = "scholarly"
    service: object = None

    def search(self, query: str, max_results: int = 5) -> List[SearchHit]:
        if self.service is None:
            from app.services.connectors.scholarly import ScholarlySearchService

            self.service = ScholarlySearchService()
        try:
            docs = self.service.search_scholarly_apis(query, limit=max_results)
        except Exception as exc:
            logger.info("scholarly search failed: %s", exc)
            return []

        return [
            SearchHit(
                url=doc.url,
                title=f"[{doc.repository}] {doc.title}",
                snippet=(doc.text or "")[:300],
                provider=self.name,
            )
            for doc in docs
            if getattr(doc, "url", "")
        ]


@dataclass
class UrlListProvider:
    """Deterministic provider: the user's own URL list."""

    urls: List[str] = field(default_factory=list)
    name: str = "urls"

    def search(self, query: str, max_results: int = 5) -> List[SearchHit]:
        return [
            SearchHit(url=u.strip(), title=u.strip(), provider=self.name)
            for u in self.urls
            if u and u.strip()
        ]


def get_provider(name: str, urls: Optional[Iterable[str]] = None) -> SearchProvider:
    """Build a provider by name.

    Args:
        name: "ddgs", "scholarly", "urls" or "none".
        urls: Required when name == "urls".
    """
    key = (name or "").strip().lower()
    if key in ("ddgs", "demo"):
        return DdgsProvider()
    if key == "scholarly":
        return ScholarlyProvider()
    if key == "urls":
        return UrlListProvider(urls=list(urls or []))
    if key in ("none", ""):
        return UrlListProvider(urls=[])
    raise ValueError(f"Unknown search provider: {name}")
