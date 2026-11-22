"""Main plagiarism detection service that orchestrates the detection pipeline."""

import json
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.document import Document, DocumentChunk
from app.models.plagiarism import PlagiarismMatch, PlagiarismReport
from app.services.plagiarism.fuzzy import ClassifiedMatch, FuzzyMatchingService
from app.services.plagiarism.report import ReportService
from app.services.plagiarism.scoring import ScoringParameters, ScoringService
from app.services.plagiarism.winnowing import WinnowingService


class PlagiarismDetectionService:
    """Main service for plagiarism detection."""

    def __init__(
        self,
        k: int = 5,  # Shingle size
        w: int = 4,  # Window size
        exact_threshold: float = 1.0,
        near_exact_threshold: float = 0.85,
        min_match_tokens: int = 8,
    ):
        """Initialize plagiarism detection service.

        Args:
            k: K-gram size for winnowing
            w: Window size for winnowing
            exact_threshold: Threshold for exact matches
            near_exact_threshold: Threshold for near-exact matches
            min_match_tokens: Minimum token count for valid match
        """
        self.winnowing = WinnowingService(k=k, w=w)
        self.fuzzy = FuzzyMatchingService(
            exact_threshold=exact_threshold,
            near_exact_threshold=near_exact_threshold,
            min_match_tokens=min_match_tokens,
        )
        self.scoring = ScoringService()
        self.report_service = ReportService()
        self.k = k
        self.w = w
        self.min_match_tokens = min_match_tokens

    def build_fingerprint_index(
        self, documents: List[Document], db: Session
    ) -> Dict[int, List[Tuple[str, int, int]]]:
        """Build inverted index of fingerprints for corpus documents.

        Args:
            documents: List of corpus documents
            db: Database session

        Returns:
            Dictionary mapping hash -> [(doc_id, position, page_number), ...]
        """
        index: Dict[int, List[Tuple[str, int, int]]] = {}

        for doc in documents:
            # Get normalized text from pages
            pages = [(page.normalized_text, page.page_number) for page in doc.pages]

            if not pages:
                continue

            # Generate fingerprints
            result, position_to_page = self.winnowing.fingerprint_document(pages)

            # Add to index
            for fp in result.fingerprints:
                page_num = position_to_page.get(fp.position, 1)
                if fp.hash_value not in index:
                    index[fp.hash_value] = []
                index[fp.hash_value].append((doc.id, fp.position, page_num))

        return index

    def find_candidate_matches(
        self,
        submitted_fingerprints: List,
        corpus_index: Dict[int, List[Tuple[str, int, int]]],
    ) -> Dict[str, List[Tuple[int, int, int]]]:
        """Find candidate matching positions between submitted and corpus.

        Args:
            submitted_fingerprints: Fingerprints from submitted document
            corpus_index: Inverted index of corpus fingerprints

        Returns:
            Dictionary mapping doc_id -> [(submitted_pos, source_pos, page), ...]
        """
        candidates: Dict[str, List[Tuple[int, int, int]]] = {}

        for fp in submitted_fingerprints:
            if fp.hash_value in corpus_index:
                for doc_id, source_pos, page_num in corpus_index[fp.hash_value]:
                    if doc_id not in candidates:
                        candidates[doc_id] = []
                    candidates[doc_id].append((fp.position, source_pos, page_num))

        return candidates

    def verify_and_classify_matches(
        self,
        submitted_tokens: List[str],
        source_documents: Dict[str, Document],
        candidates: Dict[str, List[Tuple[int, int, int]]],
        submitted_position_to_page: Dict[int, int],
        db: Session,
    ) -> List[ClassifiedMatch]:
        """Verify candidate matches and classify them.

        Args:
            submitted_tokens: Tokens from submitted document
            source_documents: Dictionary of source documents by ID
            candidates: Candidate matches from fingerprint matching
            submitted_position_to_page: Map submitted position to page number
            db: Database session

        Returns:
            List of classified matches
        """
        classified_matches = []

        for doc_id, positions in candidates.items():
            if doc_id not in source_documents:
                continue

            source_doc = source_documents[doc_id]

            # Get source tokens
            source_pages = [(page.normalized_text, page.page_number) for page in source_doc.pages]
            source_text = " ".join(text for text, _ in source_pages)
            source_tokens = self.winnowing.tokenize(source_text)

            # Build source position to page map
            source_position_to_page = {}
            current_pos = 0
            for text, page_num in source_pages:
                tokens = self.winnowing.tokenize(text)
                for i in range(len(tokens)):
                    source_position_to_page[current_pos + i] = page_num
                current_pos += len(tokens)

            # Extend and verify each candidate
            for sub_pos, src_pos, _ in positions:
                # Extend match region
                region = self.fuzzy.extend_match_region(
                    submitted_tokens, source_tokens, sub_pos, src_pos, self.k
                )

                # Classify match
                match_type = self.fuzzy.classify_match(region)

                if match_type:
                    # Get page numbers
                    sub_page = submitted_position_to_page.get(region.submitted_start, 1)
                    src_page = source_position_to_page.get(region.source_start, 1)

                    classified_matches.append(
                        ClassifiedMatch(
                            match_type=match_type,
                            submitted_start=region.submitted_start,
                            submitted_end=region.submitted_end,
                            source_start=region.source_start,
                            source_end=region.source_end,
                            submitted_text=region.submitted_text,
                            source_text=region.source_text,
                            similarity_ratio=region.similarity_ratio,
                            submitted_page=sub_page,
                            source_page=src_page,
                            source_document_id=source_doc.id,
                            source_title=source_doc.original_filename,
                        )
                    )

        return classified_matches

    def check_document(
        self,
        document_id: str,
        db: Session,
        user_id: str,
        compare_with: Optional[List[str]] = None,
        include_references: bool = True,
        online_mode: bool = False,
        custom_urls: Optional[List[str]] = None,
    ) -> str:
        """Check a document for plagiarism against corpus and optional online sources."""
        # Get submitted document
        from sqlalchemy import select

        submitted_doc = db.scalars(
            select(Document).where(Document.id == document_id)
        ).first()

        if not submitted_doc:
            raise NotFoundError("Document not found")

        if submitted_doc.owner_id != user_id:
            raise NotFoundError("Document not found")

        # Get corpus documents (exclude the submitted document itself)
        query = select(Document).where(
            Document.owner_id == user_id, Document.id != document_id
        )

        if compare_with:
            query = query.where(Document.id.in_(compare_with))

        corpus_docs = list(db.scalars(query).all())

        # Extract text from submitted document
        submitted_pages = [
            (page.normalized_text, page.page_number) for page in submitted_doc.pages
        ]
        submitted_text = " ".join(text for text, _ in submitted_pages)

        # If online mode or custom URLs requested, fetch external sources
        external_docs_info = []
        if online_mode or custom_urls:
            from app.services.connectors.scholarly import ScholarlySearchService
            from app.services.plagiarism.query_selector import QuerySelector

            scholarly = ScholarlySearchService()
            selector = QuerySelector(phrase_words=8)
            queries = selector.select_queries(submitted_text, max_queries=5)

            external_sources = []
            if custom_urls:
                external_sources.extend(scholarly.fetch_custom_urls(custom_urls))

            if online_mode:
                for q in queries:
                    external_sources.extend(scholarly.search_scholarly_apis(q, limit=2))

            # Convert external sources into temporary Document-like mock objects or indexed entries
            for ext in external_sources:
                corpus_info_dict = {
                    "id": ext.url,
                    "title": f"[{ext.repository}] {ext.title}",
                    "text": ext.text,
                }
                external_docs_info.append(corpus_info_dict)

        if not corpus_docs and not external_docs_info:
            return self._create_empty_report(
                document_id, 0, include_references, db
            )

        # Generate fingerprints for submitted document
        (
            submitted_result,
            submitted_position_to_page,
        ) = self.winnowing.fingerprint_document(submitted_pages)
        submitted_text = " ".join(text for text, _ in submitted_pages)
        submitted_tokens = self.winnowing.tokenize(submitted_text)

        # Build corpus index
        corpus_index = self.build_fingerprint_index(corpus_docs, db)

        # Find candidates
        candidates = self.find_candidate_matches(
            submitted_result.fingerprints, corpus_index
        )

        # Build source documents map
        source_docs_map = {doc.id: doc for doc in corpus_docs}

        # Verify and classify matches
        classified_matches = self.verify_and_classify_matches(
            submitted_tokens,
            source_docs_map,
            candidates,
            submitted_position_to_page,
            db,
        )

        # Add source document info to matches
        for match in classified_matches:
            source_doc = source_docs_map.get(match.source_document_id)
            if source_doc:
                match.source_document_id = source_doc.id
                match.source_title = source_doc.original_filename

        # Calculate scoring
        parameters = ScoringParameters(
            k=self.k,
            w=self.w,
            min_match_tokens=self.min_match_tokens,
            exact_threshold=1.0,
            near_exact_threshold=0.85,
            excluded_sections=[] if include_references else ["references"],
        )

        similarity_score = self.scoring.calculate_similarity_score(
            classified_matches, submitted_result.total_tokens, parameters
        )

        # Generate report
        corpus_info = [
            {"id": doc.id, "title": doc.original_filename} for doc in corpus_docs
        ]

        report = self.report_service.generate_report(
            document_id,
            classified_matches,
            similarity_score,
            corpus_info,
            include_references,
        )

        # Save report to database
        return self._save_report(report, classified_matches, db)

    def _create_empty_report(
        self, document_id: str, corpus_count: int, include_references: bool, db: Session
    ) -> str:
        """Create an empty report when no corpus available."""
        from app.models.plagiarism import PlagiarismReport as DBReport

        report_id = str(__import__("uuid").uuid4())

        db_report = DBReport(
            id=report_id,
            document_id=document_id,
            status="completed",
            corpus_scope=f"user documents ({corpus_count} docs)",
            eligible_word_count=0,
            matched_word_count=0,
            lexical_similarity_percent=0.0,
            largest_single_source_percent=0.0,
            parameters_json=json.dumps(
                {
                    "k": self.k,
                    "w": self.w,
                    "min_tokens": self.min_match_tokens,
                    "excluded": [] if include_references else ["references"],
                }
            ),
            disclaimer=self.report_service.disclaimer,
            completed_at=__import__("datetime").datetime.utcnow(),
        )

        db.add(db_report)
        db.commit()

        return report_id

    def _save_report(
        self, report, classified_matches: List[ClassifiedMatch], db: Session
    ) -> str:
        """Save report and matches to database."""
        from app.models.plagiarism import PlagiarismMatch as DBMatch
        from app.models.plagiarism import PlagiarismReport as DBReport

        # Create report record
        db_report = DBReport(
            id=report.report_id,
            document_id=report.document_id,
            status=report.status,
            corpus_scope=report.corpus_scope,
            eligible_word_count=report.eligible_word_count,
            matched_word_count=report.matched_word_count,
            lexical_similarity_percent=report.lexical_similarity_percent,
            largest_single_source_percent=report.largest_single_source_percent,
            parameters_json=json.dumps(report.parameters),
            disclaimer=report.disclaimer,
            completed_at=report.created_at,
        )

        db.add(db_report)

        # Create match records
        for match in classified_matches:
            db_match = DBMatch(
                report_id=report.report_id,
                source_document_id=match.source_document_id,
                match_type=match.match_type,
                submitted_page=match.submitted_page,
                submitted_start=match.submitted_start,
                submitted_end=match.submitted_end,
                source_page=match.source_page,
                source_start=match.source_start,
                source_end=match.source_end,
                similarity=match.similarity_ratio,
                submitted_text=match.submitted_text,
                source_text=match.source_text,
            )
            db.add(db_match)

        db.commit()

        return report.report_id
