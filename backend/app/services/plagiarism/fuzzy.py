"""Fuzzy matching service for verifying and classifying potential matches."""

from dataclasses import dataclass
from typing import List, Tuple

from rapidfuzz import fuzz


@dataclass
class MatchRegion:
    """A region of matching text between two documents."""

    submitted_start: int  # Token position in submitted document
    submitted_end: int
    source_start: int  # Token position in source document
    source_end: int
    submitted_text: str
    source_text: str
    similarity_ratio: float  # 0.0 to 1.0


@dataclass
class ClassifiedMatch:
    """A classified match with type determination."""

    match_type: str  # "exact", "near-exact"
    submitted_start: int
    submitted_end: int
    source_start: int
    source_end: int
    submitted_text: str
    source_text: str
    similarity_ratio: float
    submitted_page: int
    source_page: int
    source_document_id: Optional[str] = None
    source_title: Optional[str] = None


class FuzzyMatchingService:
    """Service for fuzzy matching and match classification."""

    def __init__(
        self,
        exact_threshold: float = 1.0,
        near_exact_threshold: float = 0.85,
        min_match_tokens: int = 8,
    ):
        """Initialize fuzzy matching service.

        Args:
            exact_threshold: Threshold for exact match (typically 1.0)
            near_exact_threshold: Threshold for near-exact match (default 0.85)
            min_match_tokens: Minimum token length for a valid match
        """
        self.exact_threshold = exact_threshold
        self.near_exact_threshold = near_exact_threshold
        self.min_match_tokens = min_match_tokens

    def extend_match_region(
        self,
        submitted_tokens: List[str],
        source_tokens: List[str],
        submitted_pos: int,
        source_pos: int,
        k: int,
    ) -> MatchRegion:
        """Extend a matching k-gram to find the full matching region.

        Args:
            submitted_tokens: All tokens from submitted document
            source_tokens: All tokens from source document
            submitted_pos: Starting position in submitted document
            source_pos: Starting position in source document
            k: Size of initial k-gram match

        Returns:
            MatchRegion with extended boundaries
        """
        # Start with the k-gram match
        sub_start = submitted_pos
        sub_end = submitted_pos + k
        src_start = source_pos
        src_end = source_pos + k

        # Extend forward
        while (
            sub_end < len(submitted_tokens)
            and src_end < len(source_tokens)
            and submitted_tokens[sub_end] == source_tokens[src_end]
        ):
            sub_end += 1
            src_end += 1

        # Extend backward
        while (
            sub_start > 0
            and src_start > 0
            and submitted_tokens[sub_start - 1] == source_tokens[src_start - 1]
        ):
            sub_start -= 1
            src_start -= 1

        # Get text
        submitted_text = " ".join(submitted_tokens[sub_start:sub_end])
        source_text = " ".join(source_tokens[src_start:src_end])

        # Calculate similarity
        similarity = fuzz.ratio(submitted_text, source_text) / 100.0

        return MatchRegion(
            submitted_start=sub_start,
            submitted_end=sub_end,
            source_start=src_start,
            source_end=src_end,
            submitted_text=submitted_text,
            source_text=source_text,
            similarity_ratio=similarity,
        )

    def classify_match(self, region: MatchRegion) -> str:
        """Classify a match region as exact, near-exact, or discard.

        Args:
            region: MatchRegion to classify

        Returns:
            Match type: "exact", "near-exact", or None (if below threshold)
        """
        # Check minimum length
        token_count = region.submitted_end - region.submitted_start
        if token_count < self.min_match_tokens:
            return None

        # Classify by similarity
        if region.similarity_ratio >= self.exact_threshold:
            return "exact"
        elif region.similarity_ratio >= self.near_exact_threshold:
            return "near-exact"
        else:
            return None

    def merge_overlapping_regions(
        self, regions: List[MatchRegion]
    ) -> List[MatchRegion]:
        """Merge overlapping match regions in the submitted document.

        This ensures no token is counted twice in similarity calculations.

        Args:
            regions: List of MatchRegion objects

        Returns:
            List of non-overlapping merged regions
        """
        if not regions:
            return []

        # Sort by submitted document position
        sorted_regions = sorted(regions, key=lambda r: (r.submitted_start, r.submitted_end))

        merged = [sorted_regions[0]]

        for current in sorted_regions[1:]:
            last_merged = merged[-1]

            # Check for overlap in submitted document
            if current.submitted_start <= last_merged.submitted_end:
                # Overlapping - merge by extending the end
                if current.submitted_end > last_merged.submitted_end:
                    # Extend merged region
                    # Keep the source with better similarity
                    if current.similarity_ratio > last_merged.similarity_ratio:
                        merged[-1] = MatchRegion(
                            submitted_start=last_merged.submitted_start,
                            submitted_end=current.submitted_end,
                            source_start=current.source_start,
                            source_end=current.source_end,
                            submitted_text=last_merged.submitted_text
                            + " "
                            + current.submitted_text[
                                (last_merged.submitted_end - current.submitted_start) :
                            ],
                            source_text=current.source_text,
                            similarity_ratio=max(
                                last_merged.similarity_ratio, current.similarity_ratio
                            ),
                        )
                    else:
                        merged[-1] = MatchRegion(
                            submitted_start=last_merged.submitted_start,
                            submitted_end=current.submitted_end,
                            source_start=last_merged.source_start,
                            source_end=last_merged.source_end
                            + (current.submitted_end - last_merged.submitted_end),
                            submitted_text=last_merged.submitted_text
                            + " "
                            + current.submitted_text[
                                (last_merged.submitted_end - current.submitted_start) :
                            ],
                            source_text=last_merged.source_text,
                            similarity_ratio=last_merged.similarity_ratio,
                        )
            else:
                # No overlap - add as new region
                merged.append(current)

        return merged

    def calculate_coverage(
        self, regions: List[MatchRegion], total_tokens: int
    ) -> Tuple[int, float]:
        """Calculate token coverage from match regions.

        Args:
            regions: List of non-overlapping MatchRegion objects
            total_tokens: Total eligible tokens in document

        Returns:
            Tuple of (covered_tokens, coverage_percentage)
        """
        if total_tokens == 0:
            return 0, 0.0

        covered_tokens = sum(
            region.submitted_end - region.submitted_start for region in regions
        )

        coverage_percentage = (covered_tokens / total_tokens) * 100.0

        return covered_tokens, coverage_percentage
