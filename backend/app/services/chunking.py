"""Text chunking service with page reference preservation."""

import re
from dataclasses import dataclass
from typing import List

from app.core.config import settings


@dataclass
class TextChunk:
    """A chunk of text with metadata."""

    chunk_id: int  # Sequential ID within document
    text: str
    page_number: int
    char_start: int  # Start position in normalized page text
    char_end: int  # End position in normalized page text
    token_count: int  # Approximate token count


class ChunkingService:
    """Service for chunking normalized text."""

    def __init__(
        self,
        chunk_size: int = settings.chunk_size,
        chunk_overlap: int = settings.chunk_overlap,
    ):
        """Initialize chunking service.

        Args:
            chunk_size: Target chunk size in tokens (approximate)
            chunk_overlap: Overlap between chunks in tokens (approximate)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, page_number: int) -> List[TextChunk]:
        """Chunk text into overlapping segments.

        Args:
            text: Normalized text to chunk
            page_number: Page number for reference

        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []

        # Split into sentences for more natural boundaries
        sentences = self._split_sentences(text)

        chunks: List[TextChunk] = []
        current_chunk: List[str] = []
        current_tokens = 0
        char_start = 0
        chunk_id = 0

        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            # If adding this sentence would exceed chunk size, save current chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                char_end = char_start + len(chunk_text)

                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        page_number=page_number,
                        char_start=char_start,
                        char_end=char_end,
                        token_count=current_tokens,
                    )
                )

                chunk_id += 1

                # Keep overlap sentences
                overlap_tokens = 0
                overlap_sentences = []

                for sent in reversed(current_chunk):
                    sent_tokens = self._estimate_tokens(sent)
                    if overlap_tokens + sent_tokens <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_tokens += sent_tokens
                    else:
                        break

                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
                char_start = char_end - sum(len(s) + 1 for s in overlap_sentences)

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            char_end = char_start + len(chunk_text)

            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    page_number=page_number,
                    char_start=char_start,
                    char_end=char_end,
                    token_count=current_tokens,
                )
            )

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting on common terminators
        # More sophisticated splitting (e.g., with spaCy) could be added later
        pattern = r"(?<=[.!?])\s+"
        sentences = re.split(pattern, text)

        # Filter out empty sentences
        return [s.strip() for s in sentences if s.strip()]

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses simple whitespace-based estimation.
        For more accuracy, could use tiktoken or tokenizers library.

        Args:
            text: Text to estimate

        Returns:
            Approximate token count
        """
        # Rough estimation: ~1.3 tokens per word for English
        words = text.split()
        return int(len(words) * 1.3)

    def chunk_pages(
        self, pages: List[tuple[str, int]]
    ) -> List[TextChunk]:
        """Chunk multiple pages of text.

        Args:
            pages: List of (text, page_number) tuples

        Returns:
            List of all chunks across pages
        """
        all_chunks: List[TextChunk] = []
        global_chunk_id = 0

        for text, page_number in pages:
            page_chunks = self.chunk_text(text, page_number)

            # Renumber chunks globally
            for chunk in page_chunks:
                chunk.chunk_id = global_chunk_id
                all_chunks.append(chunk)
                global_chunk_id += 1

        return all_chunks
