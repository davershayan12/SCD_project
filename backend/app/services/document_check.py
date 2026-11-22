"""Orchestration service for the complete Document Check feature (Web Plagiarism + AI Detection)."""

from __future__ import annotations

import concurrent.futures
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.ai_detector import AIDetectorService
from app.services.document_cleaner import DocumentCleaner
from app.services.fetcher.safe_fetcher import SafeFetcher, FetchError
from app.services.plagiarism.query_selector import QuerySelector
from app.services.plagiarism.winnowing import WinnowingService
from app.services.plagiarism.fuzzy import FuzzyMatchingService
from app.services.plagiarism.scoring import ScoringService
from app.services.web_search.providers import get_provider, SearchHit

logger = logging.getLogger(__name__)


@dataclass
class StageStatus:
    """Status counters and diagnostics per pipeline stage."""

    queries_run: int = 0
    search_hits_found: int = 0
    pages_attempted: int = 0
    pages_fetched_ok: int = 0
    pages_failed: int = 0
    failure_reasons: Dict[str, int] = field(default_factory=dict)
    query_details: List[Dict[str, Any]] = field(default_factory=list)
    fetch_details: List[Dict[str, Any]] = field(default_factory=list)

    def record_failure(self, reason: str) -> None:
        self.pages_failed += 1
        self.failure_reasons[reason] = self.failure_reasons.get(reason, 0) + 1


@dataclass
class DocumentCheckResult:
    """Complete combined result of web plagiarism search and AI detection."""

    document_id: str
    filename: str
    status: str  # "completed", "partial", "inconclusive", "failed"
    corpus_scope: str
    eligible_word_count: int
    matched_word_count: int
    lexical_similarity_percent: float
    largest_single_source_percent: float
    matches: List[Dict[str, Any]]
    ai_detection: Dict[str, Any]
    status_diagnostics: Dict[str, Any]
    disclaimer: str
    created_at: str


class DocumentCheckOrchestrator:
    """Orchestrates web search, safe concurrent fetching, matching, and AI detection."""

    DISCLAIMER = (
        "Similarity is not a determination of plagiarism. "
        "No matches found in the sources searched. "
        "AI-likelihood is a statistical indicator, not proof of authorship."
    )

    def __init__(
        self,
        search_provider: Optional[str] = None,
        custom_urls: Optional[List[str]] = None,
        diagnostics_mode: bool = True,
    ):
        self.search_provider_name = search_provider or settings.web_search_provider
        self.custom_urls = custom_urls or []
        self.diagnostics_mode = diagnostics_mode
        self.fetcher = SafeFetcher(
            max_bytes=settings.web_fetch_max_bytes,
            timeout=settings.web_fetch_timeout,
        )
        self.query_selector = QuerySelector(phrase_words=8)
        self.winnowing = WinnowingService(k=5, w=4)
        self.fuzzy = FuzzyMatchingService(exact_threshold=1.0, near_exact_threshold=0.85, min_match_tokens=8)
        self.scoring = ScoringService()
        self.ai_detector = AIDetectorService()

    def run_check(self, document_id: str, filename: str, pages: List[tuple[str, int]]) -> DocumentCheckResult:
        """Execute the full document check pipeline with instrumentation."""
        stage = StageStatus()

        # 1. Extract text and tokens
        raw_text = " ".join(text for text, _ in pages)
        submitted_text = DocumentCleaner.strip_references(raw_text)
        submitted_tokens = self.winnowing.tokenize(submitted_text)
        eligible_words = len(submitted_tokens)

        # 2. Run AI detection independently
        try:
            ai_result = self.ai_detector.analyze_text(submitted_text)
        except Exception as e:
            logger.error("AI detection failed: %s", e)
            ai_result = {
                "overall_score": 0.0,
                "status": "inconclusive",
                "fallback_used": True,
                "fallback_reason": str(e),
                "paragraphs": [],
                "disclaimer": AIDetectorService.DISCLAIMER,
            }

        # 3. Web Search & Fetch Pipeline
        hits: List[SearchHit] = []
        try:
            if self.custom_urls:
                from app.services.web_search.providers import UrlListProvider
                url_prov = UrlListProvider(self.custom_urls)
                custom_hits = url_prov.search(submitted_text[:100], max_results=len(self.custom_urls))
                hits.extend(custom_hits)
                stage.queries_run += 1
                if self.diagnostics_mode:
                    stage.query_details.append({
                        "query": "[custom URLs list]",
                        "provider": "urls",
                        "hits": len(custom_hits),
                    })

            if self.search_provider_name and self.search_provider_name != "none":
                provider = get_provider(self.search_provider_name, urls=self.custom_urls)
                queries = self.query_selector.select_queries(submitted_text, max_queries=settings.web_search_max_queries)
                stage.queries_run = len(queries)

                for q in queries:
                    import time
                    start_t = time.time()
                    try:
                        results = provider.search(q, max_results=3)
                        duration_ms = (time.time() - start_t) * 1000
                        hits.extend(results)
                        if self.diagnostics_mode:
                            stage.query_details.append({
                                "query": q,
                                "provider": provider.name,
                                "hits": len(results),
                                "duration_ms": round(duration_ms, 1),
                            })
                    except Exception as q_exc:
                        if self.diagnostics_mode:
                            stage.query_details.append({
                                "query": q,
                                "provider": provider.name,
                                "error": str(q_exc),
                            })
        except Exception as e:
            logger.error("Web search stage failed: %s", e)

        # Deduplicate hits by URL
        unique_hits: Dict[str, SearchHit] = {h.url: h for h in hits if h.url}
        stage.search_hits_found = len(unique_hits)

        # 4. Concurrent Safe Fetching with cleaning
        fetched_sources: List[Dict[str, Any]] = []

        def fetch_one(hit: SearchHit):
            stage.pages_attempted += 1
            try:
                res = self.fetcher.fetch_url(hit.url)
                cleaned_text = DocumentCleaner.clean_html(res.text)
                stage.pages_fetched_ok += 1
                if self.diagnostics_mode:
                    stage.fetch_details.append({
                        "url": hit.url,
                        "status": res.status_code,
                        "bytes": len(res.content),
                        "extracted_words": len(cleaned_text.split()),
                    })
                return {"url": hit.url, "title": hit.title or hit.url, "text": cleaned_text}
            except FetchError as fe:
                stage.record_failure(str(fe))
                if self.diagnostics_mode:
                    stage.fetch_details.append({"url": hit.url, "error": str(fe)})
            except Exception as exc:
                err_str = type(exc).__name__
                stage.record_failure(err_str)
                if self.diagnostics_mode:
                    stage.fetch_details.append({"url": hit.url, "error": err_str})
            return None

        if unique_hits:
            with concurrent.futures.ThreadPoolExecutor(max_workers=settings.web_fetch_workers) as executor:
                futures = [executor.submit(fetch_one, hit) for hit in unique_hits.values()]
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res:
                        fetched_sources.append(res)

        # 5. Matching & Scoring against fetched web pages
        all_matches = []
        for src in fetched_sources:
            src_text = src["text"]
            src_tokens = self.winnowing.tokenize(src_text)
            if not src_tokens:
                continue

            sub_res = self.winnowing.fingerprint(submitted_text)
            src_res = self.winnowing.fingerprint(src_text)
            src_hashes = {fp.hash_value: fp.position for fp in src_res.fingerprints}

            for fp in sub_res.fingerprints:
                if fp.hash_value in src_hashes:
                    src_pos = src_hashes[fp.hash_value]
                    region = self.fuzzy.extend_match_region(
                        submitted_tokens, src_tokens, fp.position, src_pos, 5
                    )
                    match_type = self.fuzzy.classify_match(region)
                    if match_type:
                        all_matches.append({
                            "match_type": match_type,
                            "submitted_page": 1,
                            "submitted_span": [region.submitted_start, region.submitted_end],
                            "source_document_id": src["url"],
                            "source_title": src["title"],
                            "source_page": 1,
                            "similarity": region.similarity_ratio,
                            "submitted_text": region.submitted_text,
                            "source_text": region.source_text,
                        })

        class MockMatch:
            def __init__(self, m):
                self.submitted_start = m["submitted_span"][0]
                self.submitted_end = m["submitted_span"][1]

        mock_objects = [MockMatch(m) for m in all_matches]
        merged_spans = self.scoring.merge_overlapping_spans(mock_objects)
        matched_words = sum(end - start for start, end in merged_spans)

        lexical_similarity = (matched_words / eligible_words * 100.0) if eligible_words > 0 else 0.0

        # Determine status
        status = "completed"
        if stage.search_hits_found == 0 or (stage.pages_attempted > 0 and stage.pages_fetched_ok == 0):
            status = "inconclusive"
        elif stage.pages_failed > 0:
            status = "partial"

        corpus_scope = f"live web search ({stage.pages_fetched_ok} pages successfully fetched from {stage.search_hits_found} search hits)"

        diagnostics_payload = {
            "queries_run": stage.queries_run,
            "search_hits_found": stage.search_hits_found,
            "pages_attempted": stage.pages_attempted,
            "pages_fetched_ok": stage.pages_fetched_ok,
            "pages_failed": stage.pages_failed,
            "failure_reasons": stage.failure_reasons,
        }
        if self.diagnostics_mode:
            diagnostics_payload["query_details"] = stage.query_details
            diagnostics_payload["fetch_details"] = stage.fetch_details

        return DocumentCheckResult(
            document_id=document_id,
            filename=filename,
            status=status,
            corpus_scope=corpus_scope,
            eligible_word_count=eligible_words,
            matched_word_count=matched_words,
            lexical_similarity_percent=round(lexical_similarity, 1),
            largest_single_source_percent=round(lexical_similarity, 1),
            matches=all_matches[:50],
            ai_detection=ai_result,
            status_diagnostics=diagnostics_payload,
            disclaimer=self.DISCLAIMER,
            created_at=datetime.utcnow().isoformat(),
        )
