"""Winnowing fingerprinting algorithm for document similarity detection.

Winnowing creates a robust fingerprint of a document that can detect copies
even with small modifications. It guarantees that any match of length >= w+k-1
will be detected, where k is the shingle size and w is the window size.

References:
- Schleimer, S., Wilkerson, D. S., & Aiken, A. (2003).
  Winnowing: local algorithms for document fingerprinting.
"""

import hashlib
from dataclasses import dataclass
from typing import List, Set, Tuple


@dataclass
class Fingerprint:
    """A single fingerprint from the winnowing algorithm."""

    hash_value: int
    position: int  # Position in the document (token index)
    text: str  # The actual k-gram text for debugging


@dataclass
class WinnowingResult:
    """Result of winnowing fingerprinting."""

    fingerprints: List[Fingerprint]
    total_tokens: int
    total_shingles: int
    k: int  # Shingle size (k-gram)
    w: int  # Window size


class WinnowingService:
    """Service for generating winnowing fingerprints from text."""

    def __init__(self, k: int = 5, w: int = 4):
        """Initialize winnowing service.

        Args:
            k: Size of k-grams (shingles). Default 5 words.
            w: Window size for winnowing. Default 4.
               Guarantees detection of matches >= k+w-1 tokens long.
        """
        self.k = k
        self.w = w

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into normalized word tokens.

        Args:
            text: Input text (should be normalized)

        Returns:
            List of lowercase word tokens
        """
        # Simple whitespace tokenization + lowercase
        # More sophisticated tokenization could be added later
        tokens = text.lower().split()
        return [t for t in tokens if t]  # Remove empty strings

    def create_shingles(self, tokens: List[str]) -> List[Tuple[str, int]]:
        """Create k-gram shingles from tokens.

        Args:
            tokens: List of word tokens

        Returns:
            List of (shingle_text, position) tuples
        """
        if len(tokens) < self.k:
            return []

        shingles = []
        for i in range(len(tokens) - self.k + 1):
            shingle = " ".join(tokens[i : i + self.k])
            shingles.append((shingle, i))

        return shingles

    def hash_shingle(self, shingle: str) -> int:
        """Hash a shingle to a 64-bit integer.

        Args:
            shingle: Shingle text

        Returns:
            64-bit hash value
        """
        # Use MD5 for speed, take first 8 bytes as 64-bit int
        hash_bytes = hashlib.md5(shingle.encode("utf-8")).digest()[:8]
        return int.from_bytes(hash_bytes, byteorder="big")

    def winnow(
        self, shingle_hashes: List[Tuple[int, int, str]]
    ) -> List[Fingerprint]:
        """Apply winnowing algorithm to select representative fingerprints.

        Winnowing guarantees that any match of length >= w+k-1 will be detected.

        Args:
            shingle_hashes: List of (hash, position, text) tuples

        Returns:
            List of selected fingerprints
        """
        if len(shingle_hashes) < self.w:
            # If we have fewer shingles than window size, keep all
            return [
                Fingerprint(hash_value=h, position=pos, text=txt)
                for h, pos, txt in shingle_hashes
            ]

        fingerprints = []
        min_hash_in_window = None
        min_position = -1

        for i in range(len(shingle_hashes) - self.w + 1):
            # Get window of w hashes
            window = shingle_hashes[i : i + self.w]

            # Find minimum hash in window (with rightmost position if tie)
            current_min = min(window, key=lambda x: (x[0], -x[1]))
            current_min_hash, current_min_pos, current_min_text = current_min

            # Only add if this is a new minimum position
            if current_min_pos != min_position:
                fingerprints.append(
                    Fingerprint(
                        hash_value=current_min_hash,
                        position=current_min_pos,
                        text=current_min_text,
                    )
                )
                min_position = current_min_pos
                min_hash_in_window = current_min_hash

        return fingerprints

    def fingerprint(self, text: str) -> WinnowingResult:
        """Generate winnowing fingerprints for text.

        Args:
            text: Input text (should be normalized)

        Returns:
            WinnowingResult with fingerprints and metadata
        """
        # Tokenize
        tokens = self.tokenize(text)

        if len(tokens) < self.k:
            # Text too short for k-grams
            return WinnowingResult(
                fingerprints=[],
                total_tokens=len(tokens),
                total_shingles=0,
                k=self.k,
                w=self.w,
            )

        # Create shingles
        shingles = self.create_shingles(tokens)

        # Hash shingles
        shingle_hashes = [
            (self.hash_shingle(shingle), pos, shingle) for shingle, pos in shingles
        ]

        # Apply winnowing
        fingerprints = self.winnow(shingle_hashes)

        return WinnowingResult(
            fingerprints=fingerprints,
            total_tokens=len(tokens),
            total_shingles=len(shingles),
            k=self.k,
            w=self.w,
        )

    def fingerprint_document(
        self, pages: List[Tuple[str, int]]
    ) -> Tuple[WinnowingResult, dict]:
        """Generate fingerprints for a multi-page document.

        Args:
            pages: List of (text, page_number) tuples

        Returns:
            Tuple of (WinnowingResult, position_to_page_map)
            position_to_page_map maps token position to page number
        """
        # Concatenate all pages with tracking
        all_tokens = []
        position_to_page = {}
        current_position = 0

        for text, page_number in pages:
            tokens = self.tokenize(text)
            for i, token in enumerate(tokens):
                position_to_page[current_position + i] = page_number
            all_tokens.extend(tokens)
            current_position += len(tokens)

        # Create shingles
        if len(all_tokens) < self.k:
            return (
                WinnowingResult(
                    fingerprints=[],
                    total_tokens=len(all_tokens),
                    total_shingles=0,
                    k=self.k,
                    w=self.w,
                ),
                position_to_page,
            )

        shingles = []
        for i in range(len(all_tokens) - self.k + 1):
            shingle = " ".join(all_tokens[i : i + self.k])
            shingles.append((shingle, i))

        # Hash shingles
        shingle_hashes = [
            (self.hash_shingle(shingle), pos, shingle) for shingle, pos in shingles
        ]

        # Apply winnowing
        fingerprints = self.winnow(shingle_hashes)

        result = WinnowingResult(
            fingerprints=fingerprints,
            total_tokens=len(all_tokens),
            total_shingles=len(shingles),
            k=self.k,
            w=self.w,
        )

        return result, position_to_page
