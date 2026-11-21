"""Text normalization service with offset tracking."""

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class OffsetMapping:
    """Mapping from normalized position to original position."""

    normalized_start: int
    normalized_end: int
    original_start: int
    original_end: int
    page_number: int


@dataclass
class NormalizedText:
    """Normalized text with offset mappings."""

    text: str
    original_text: str
    page_number: int
    mappings: List[OffsetMapping]


class NormalizationService:
    """Service for normalizing extracted text."""

    # Common ligatures to expand
    LIGATURES = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬀ": "ff",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "ﬅ": "ft",
        "ﬆ": "st",
        "Ꜳ": "AA",
        "ꜳ": "aa",
        "Æ": "AE",
        "æ": "ae",
        "Œ": "OE",
        "œ": "oe",
    }

    def normalize(
        self, text: str, page_number: int, dehyphenate: bool = True
    ) -> NormalizedText:
        """Normalize text with offset tracking.

        Args:
            text: Raw text to normalize
            page_number: Page number for offset tracking
            dehyphenate: Whether to remove line-break hyphenation

        Returns:
            NormalizedText with mappings
        """
        original_text = text
        mappings: List[OffsetMapping] = []

        # Step 1: Unicode normalization (NFKC)
        text = unicodedata.normalize("NFKC", text)

        # Step 2: Fix ligatures
        text = self._fix_ligatures(text)

        # Step 3: De-hyphenate line breaks
        if dehyphenate:
            text = self._dehyphenate(text)

        # Step 4: Collapse whitespace
        text = self._collapse_whitespace(text)

        # Step 5: Clean up punctuation spacing
        text = self._clean_punctuation(text)

        # For Phase 1, we create a simple 1:1 mapping
        # In production, this should track character-level changes
        if text:
            mappings.append(
                OffsetMapping(
                    normalized_start=0,
                    normalized_end=len(text),
                    original_start=0,
                    original_end=len(original_text),
                    page_number=page_number,
                )
            )

        return NormalizedText(
            text=text,
            original_text=original_text,
            page_number=page_number,
            mappings=mappings,
        )

    def _fix_ligatures(self, text: str) -> str:
        """Replace ligatures with separate characters.

        Args:
            text: Text containing ligatures

        Returns:
            Text with ligatures expanded
        """
        for ligature, replacement in self.LIGATURES.items():
            text = text.replace(ligature, replacement)
        return text

    def _dehyphenate(self, text: str) -> str:
        """Remove hyphenation at line breaks.

        Args:
            text: Text with potential hyphenation

        Returns:
            Text with line-break hyphens removed
        """
        # Match word-hyphen-newline-word pattern
        # Be conservative: only remove if followed by lowercase letter
        text = re.sub(r"(\w)-\n([a-z])", r"\1\2", text)
        return text

    def _collapse_whitespace(self, text: str) -> str:
        """Collapse multiple spaces while preserving paragraphs.

        Args:
            text: Text with irregular whitespace

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r"[ \t]+", " ", text)

        # Preserve paragraph breaks (double newline)
        # but remove single newlines within paragraphs
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

        # Normalize paragraph breaks
        text = re.sub(r"\n{2,}", "\n\n", text)

        return text.strip()

    def _clean_punctuation(self, text: str) -> str:
        """Clean up punctuation spacing.

        Args:
            text: Text with irregular punctuation spacing

        Returns:
            Text with cleaned punctuation
        """
        # Remove spaces before punctuation
        text = re.sub(r"\s+([.,;:!?])", r"\1", text)

        # Ensure space after punctuation (if followed by word char)
        text = re.sub(r"([.,;:!?])([A-Za-z])", r"\1 \2", text)

        return text

    def normalize_batch(
        self, texts: List[Tuple[str, int]], dehyphenate: bool = True
    ) -> List[NormalizedText]:
        """Normalize multiple texts.

        Args:
            texts: List of (text, page_number) tuples
            dehyphenate: Whether to remove line-break hyphenation

        Returns:
            List of NormalizedText objects
        """
        return [
            self.normalize(text, page_num, dehyphenate)
            for text, page_num in texts
        ]
