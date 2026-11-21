"""Plagiarism scoring service with transparent methodology."""

from dataclasses import dataclass
from typing import Dict, List

from app.services.plagiarism.fuzzy import ClassifiedMatch, MatchRegion


@dataclass
class ScoringParameters:
    """Parameters used for scoring."""

    k: int  # Shingle size
    w: int  # Window size
    min_match_tokens: int
    exact_threshold: float
    near_exact_threshold: float
    excluded_sections: List[str]  # e.g., ["references"]


@dataclass
class SourceContribution:
    """Contribution from a single source document."""

    source_document_id: str
    source_title: str
    matched_tokens: int
    percentage_of_submitted: float
    match_count: int


@dataclass
class SimilarityScore:
    """Complete similarity scoring result."""

    eligible_tokens: int
    matched_tokens: int
    lexical_similarity_percent: float
    largest_single_source_percent: float
    largest_source_id: str
    source_contributions: List[SourceContribution]
    parameters: ScoringParameters
    total_matches: int


class ScoringService:
    """Service for scoring plagiarism detection results."""

    def __init__(self):
        """Initialize scoring service."""
        pass

    def merge_overlapping_spans(
        self, matches: List[ClassifiedMatch]
    ) -> List[tuple[int, int]]:
        """Merge overlapping token spans to avoid double-counting.

        Args:
            matches: List of classified matches

        Returns:
            List of (start, end) tuples for non-overlapping spans
        """
        if not matches:
            return []

        # Extract spans and sort by start position
        spans = [(m.submitted_start, m.submitted_end) for m in matches]
        spans.sort()

        merged = [spans[0]]

        for current_start, current_end in spans[1:]:
            last_start, last_end = merged[-1]

            if current_start <= last_end:
                # Overlapping - merge
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                # No overlap - add new span
                merged.append((current_start, current_end))

        return merged

    def calculate_source_contributions(
        self, matches: List[ClassifiedMatch], eligible_tokens: int
    ) -> List[SourceContribution]:
        """Calculate contribution from each source document.

        Args:
            matches: List of classified matches
            eligible_tokens: Total eligible tokens in submitted document

        Returns:
            List of source contributions, sorted by percentage descending
        """
        # Group matches by source
        source_groups: Dict[str, List[ClassifiedMatch]] = {}
        source_titles: Dict[str, str] = {}

        for match in matches:
            source_id = match.source_document_id if hasattr(match, "source_document_id") else "unknown"
            if source_id not in source_groups:
                source_groups[source_id] = []
                source_titles[source_id] = (
                    match.source_title if hasattr(match, "source_title") else source_id
                )
            source_groups[source_id].append(match)

        # Calculate contribution for each source
        contributions = []
        for source_id, source_matches in source_groups.items():
            # Merge overlapping spans for this source
            spans = self.merge_overlapping_spans(source_matches)

            # Count total matched tokens
            matched_tokens = sum(end - start for start, end in spans)

            # Calculate percentage
            percentage = (
                (matched_tokens / eligible_tokens * 100.0) if eligible_tokens > 0 else 0.0
            )

            contributions.append(
                SourceContribution(
                    source_document_id=source_id,
                    source_title=source_titles[source_id],
                    matched_tokens=matched_tokens,
                    percentage_of_submitted=percentage,
                    match_count=len(source_matches),
                )
            )

        # Sort by percentage descending
        contributions.sort(key=lambda c: c.percentage_of_submitted, reverse=True)

        return contributions

    def calculate_similarity_score(
        self,
        matches: List[ClassifiedMatch],
        eligible_tokens: int,
        parameters: ScoringParameters,
    ) -> SimilarityScore:
        """Calculate overall similarity score with transparent methodology.

        Args:
            matches: List of all classified matches
            eligible_tokens: Total eligible tokens (after exclusions)
            parameters: Scoring parameters used

        Returns:
            SimilarityScore with all metrics
        """
        if eligible_tokens == 0:
            return SimilarityScore(
                eligible_tokens=0,
                matched_tokens=0,
                lexical_similarity_percent=0.0,
                largest_single_source_percent=0.0,
                largest_source_id=None,
                source_contributions=[],
                parameters=parameters,
                total_matches=0,
            )

        # Merge all overlapping spans across all sources
        merged_spans = self.merge_overlapping_spans(matches)

        # Count total matched tokens (no double-counting)
        matched_tokens = sum(end - start for start, end in merged_spans)

        # Calculate overall similarity percentage
        lexical_similarity_percent = (matched_tokens / eligible_tokens) * 100.0

        # Calculate per-source contributions
        source_contributions = self.calculate_source_contributions(
            matches, eligible_tokens
        )

        # Find largest single source
        largest_source_percent = 0.0
        largest_source_id = None
        if source_contributions:
            largest = source_contributions[0]
            largest_source_percent = largest.percentage_of_submitted
            largest_source_id = largest.source_document_id

        return SimilarityScore(
            eligible_tokens=eligible_tokens,
            matched_tokens=matched_tokens,
            lexical_similarity_percent=lexical_similarity_percent,
            largest_single_source_percent=largest_source_percent,
            largest_source_id=largest_source_id,
            source_contributions=source_contributions,
            parameters=parameters,
            total_matches=len(matches),
        )
