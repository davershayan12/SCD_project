"""Evidence verification service using deterministic text matching."""

from dataclasses import dataclass
from typing import List, Optional
from rapidfuzz import fuzz

from app.services.normalization import NormalizationService


@dataclass
class EvidenceItem:
    """An extracted evidence claim with page and quote."""

    page: int
    quote: str


@dataclass
class VerifiedEvidence:
    """Result of evidence verification."""

    is_verified: bool
    similarity_ratio: float
    matched_page: int
    error_message: Optional[str] = None


class EvidenceVerificationService:
    """Service for verifying extracted evidence quotes against document text."""

    def __init__(self, fuzzy_threshold: float = 0.85):
        """Initialize evidence verification service.

        Args:
            fuzzy_threshold: Minimum similarity ratio to consider quote verified
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.normalizer = NormalizationService()

    def verify_quote(
        self,
        quote: str,
        claimed_page: int,
        document_pages: List[tuple[str, int]],
    ) -> VerifiedEvidence:
        """Verify that a quote exists on the claimed page (or nearby pages).

        Args:
            quote: Extracted quote text
            claimed_page: Claimed page number
            document_pages: List of (page_text, page_number) tuples

        Returns:
            VerifiedEvidence result
        """
        if not quote.strip():
            return VerifiedEvidence(
                is_verified=False,
                similarity_ratio=0.0,
                matched_page=claimed_page,
                error_message="Empty quote",
            )

        norm_quote = self.normalizer.normalize(quote, claimed_page).text.lower()

        # Find page text for claimed page
        target_page_text = ""
        for text, page_num in document_pages:
            if page_num == claimed_page:
                target_page_text = self.normalizer.normalize(text, page_num).text.lower()
                break

        if not target_page_text:
            # Page not found, search all pages
            best_ratio = 0.0
            best_page = claimed_page
            for text, page_num in document_pages:
                page_norm = self.normalizer.normalize(text, page_num).text.lower()
                ratio = fuzz.partial_ratio(norm_quote, page_norm) / 100.0
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_page = page_num

            if best_ratio >= self.fuzzy_threshold:
                return VerifiedEvidence(
                    is_verified=True,
                    similarity_ratio=best_ratio,
                    matched_page=best_page,
                )
            else:
                return VerifiedEvidence(
                    is_verified=False,
                    similarity_ratio=best_ratio,
                    matched_page=claimed_page,
                    error_message=f"Quote not found on claimed page {claimed_page} (best match page {best_page} ratio {best_ratio:.2f})",
                )

        # Check against target page
        ratio = fuzz.partial_ratio(norm_quote, target_page_text) / 100.0

        if ratio >= self.fuzzy_threshold:
            return VerifiedEvidence(
                is_verified=True,
                similarity_ratio=ratio,
                matched_page=claimed_page,
            )

        # If not on exact page, check adjacent pages (±1)
        for text, page_num in document_pages:
            if abs(page_num - claimed_page) == 1:
                adj_norm = self.normalizer.normalize(text, page_num).text.lower()
                adj_ratio = fuzz.partial_ratio(norm_quote, adj_norm) / 100.0
                if adj_ratio >= self.fuzzy_threshold:
                    return VerifiedEvidence(
                        is_verified=True,
                        similarity_ratio=adj_ratio,
                        matched_page=page_num,
                    )

        return VerifiedEvidence(
            is_verified=False,
            similarity_ratio=ratio,
            matched_page=claimed_page,
            error_message=f"Quote verification failed: similarity ratio {ratio:.2f} below threshold {self.fuzzy_threshold}",
        )
