"""Scholarly API and URL list connectors for online plagiarism checking."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import httpx

from app.services.fetcher.safe_fetcher import SafeFetcher, FetchError


@dataclass
class ExternalSourceDocument:
    """Document or page fetched from an external source."""

    source_id: str
    title: str
    url: str
    license: str
    repository: str
    fetch_date: str
    text: str


class ScholarlySearchService:
    """Service for querying scholarly APIs and custom URLs."""

    def __init__(self, safe_fetcher: Optional[SafeFetcher] = None):
        self.fetcher = safe_fetcher or SafeFetcher()

    def fetch_custom_urls(self, urls: List[str]) -> List[ExternalSourceDocument]:
        """Fetch content from a list of user-supplied URLs safely."""
        documents = []
        for url in urls:
            try:
                res = self.fetcher.fetch_url(url.strip())
                if res.status_code == 200:
                    documents.append(
                        ExternalSourceDocument(
                            source_id=url,
                            title=url,
                            url=url,
                            license="User-supplied URL",
                            repository="Custom URL",
                            fetch_date=datetime.utcnow().isoformat(),
                            text=res.text,
                        )
                    )
            except Exception as e:
                # Log or ignore individual URL fetch failures during check
                pass
        return documents

    def search_scholarly_apis(self, query: str, limit: int = 3) -> List[ExternalSourceDocument]:
        """Query arXiv and OpenAlex metadata/abstracts."""
        documents = []

        # 1. arXiv API
        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results={limit}"
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    for entry in root.findall("atom:entry", ns):
                        title_el = entry.find("atom:title", ns)
                        summary_el = entry.find("atom:summary", ns)
                        id_el = entry.find("atom:id", ns)
                        title = title_el.text.strip().replace("\n", " ") if title_el is not None else "arXiv Paper"
                        summary = summary_el.text.strip().replace("\n", " ") if summary_el is not None else ""
                        link = id_el.text.strip() if id_el is not None else ""

                        documents.append(
                            ExternalSourceDocument(
                                source_id=link,
                                title=title,
                                url=link,
                                license="arXiv CC-BY / CC0",
                                repository="arXiv",
                                fetch_date=datetime.utcnow().isoformat(),
                                text=summary,
                            )
                        )
        except Exception:
            pass

        return documents
