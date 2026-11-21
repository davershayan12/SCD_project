"""Open-access corpus connectors interface and implementations."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import httpx

logger = logging.getLogger(__name__)


@dataclass
class ExternalSourceDocument:
    """Document fetched from an external open-access API."""

    source_id: str
    title: str
    abstract: Optional[str]
    url: str
    license: str
    repository: str  # e.g., "arXiv", "OpenAlex", "Semantic Scholar"
    fetch_date: str
    full_text_available: bool = False
    full_text: Optional[str] = None


class BaseCorpusConnector(ABC):
    """Abstract base class for open-access corpus connectors."""

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[ExternalSourceDocument]:
        """Search external repository for relevant open-access papers."""
        pass


class ArXivConnector(BaseCorpusConnector):
    """Connector for arXiv API (CC0 / CC-BY licenses)."""

    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"

    def search(self, query: str, limit: int = 5) -> List[ExternalSourceDocument]:
        """Search arXiv API."""
        try:
            params = {
                "search_query": f"all:{query}",
                "max_results": limit,
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.base_url, params=params)
                if response.status_code != 200:
                    return []

                # Simple XML parsing for arXivAtom response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                namespace = {"atom": "http://www.w3.org/2005/Atom"}

                documents = []
                for entry in root.findall("atom:entry", namespace):
                    title_elem = entry.find("atom:title", namespace)
                    summary_elem = entry.find("atom:summary", namespace)
                    id_elem = entry.find("atom:id", namespace)

                    title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else "Untitled"
                    abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else None
                    url = id_elem.text.strip() if id_elem is not None else ""

                    documents.append(
                        ExternalSourceDocument(
                            source_id=url.split("/")[-1],
                            title=title,
                            abstract=abstract,
                            url=url,
                            license="arXiv CC-BY / CC0 (permissive)",
                            repository="arXiv",
                            fetch_date=datetime.utcnow().isoformat(),
                            full_text_available=False,  # Metadata only unless PDF fetched
                        )
                    )

                return documents
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []


class OpenAlexConnector(BaseCorpusConnector):
    """Connector for OpenAlex API (CC0 metadata)."""

    def __init__(self):
        self.base_url = "https://api.openalex.org/works"

    def search(self, query: str, limit: int = 5) -> List[ExternalSourceDocument]:
        """Search OpenAlex API."""
        try:
            params = {
                "search": query,
                "per-page": limit,
            }
            headers = {"User-Agent": "ResearchRadar/0.1.0 (mailto:research@example.com)"}
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.base_url, params=params, headers=headers)
                if response.status_code != 200:
                    return []

                data = response.json()
                results = data.get("results", [])

                documents = []
                for work in results:
                    title = work.get("title", "Untitled")
                    work_id = work.get("id", "")
                    doi = work.get("doi", work_id)

                    # Extract abstract if available from inverted index
                    abstract = None
                    ab_inverted = work.get("abstract_inverted_index")
                    if ab_inverted:
                        # Reconstruct abstract from inverted index
                        word_indices = []
                        for word, indices in ab_inverted.items():
                            for idx in indices:
                                word_indices.append((idx, word))
                        word_indices.sort(key=lambda x: x[0])
                        abstract = " ".join([w for _, w in word_indices])

                    documents.append(
                        ExternalSourceDocument(
                            source_id=work_id,
                            title=title,
                            abstract=abstract,
                            url=doi,
                            license="OpenAlex CC0 Metadata",
                            repository="OpenAlex",
                            fetch_date=datetime.utcnow().isoformat(),
                            full_text_available=False,
                        )
                    )

                return documents
        except Exception as e:
            logger.error(f"OpenAlex search failed: {e}")
            return []
