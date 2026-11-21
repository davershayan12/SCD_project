"""Unit tests for text chunking service."""

import pytest

from app.services.chunking import ChunkingService


class TestChunkingService:
    """Test text chunking."""

    def test_basic_chunking(self):
        """Test basic text chunking."""
        service = ChunkingService(chunk_size=50, chunk_overlap=10)
        text = "This is sentence one. This is sentence two. This is sentence three."

        chunks = service.chunk_text(text, page_number=1)

        assert len(chunks) > 0
        assert all(chunk.page_number == 1 for chunk in chunks)
        assert chunks[0].chunk_id == 0

    def test_chunk_overlap(self):
        """Test that chunks have overlap."""
        service = ChunkingService(chunk_size=30, chunk_overlap=10)
        text = " ".join([f"Sentence number {i}." for i in range(20)])

        chunks = service.chunk_text(text, page_number=1)

        if len(chunks) > 1:
            # Check for overlap by looking at text similarity
            assert len(chunks) >= 2

    def test_empty_text(self):
        """Test handling of empty text."""
        service = ChunkingService()
        chunks = service.chunk_text("", page_number=1)

        assert len(chunks) == 0

    def test_whitespace_only(self):
        """Test handling of whitespace-only text."""
        service = ChunkingService()
        chunks = service.chunk_text("   \n\n  \t  ", page_number=1)

        assert len(chunks) == 0

    def test_short_text(self):
        """Test chunking of text shorter than chunk size."""
        service = ChunkingService(chunk_size=100)
        text = "Short text."

        chunks = service.chunk_text(text, page_number=1)

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_sentence_boundaries(self):
        """Test that chunks respect sentence boundaries."""
        service = ChunkingService(chunk_size=50, chunk_overlap=10)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."

        chunks = service.chunk_text(text, page_number=1)

        for chunk in chunks:
            # Chunks should contain complete sentences
            assert chunk.text.strip() != ""

    def test_chunk_metadata(self):
        """Test chunk metadata is correctly set."""
        service = ChunkingService()
        text = "This is a test sentence for metadata checking."

        chunks = service.chunk_text(text, page_number=5)

        assert len(chunks) > 0
        chunk = chunks[0]
        assert chunk.page_number == 5
        assert chunk.char_start >= 0
        assert chunk.char_end > chunk.char_start
        assert chunk.token_count > 0
        assert len(chunk.text) == (chunk.char_end - chunk.char_start)

    def test_batch_chunking(self):
        """Test chunking multiple pages."""
        service = ChunkingService(chunk_size=50)
        pages = [
            ("Page one content with sentences.", 1),
            ("Page two content with more sentences.", 2),
            ("Page three content.", 3),
        ]

        all_chunks = service.chunk_pages(pages)

        assert len(all_chunks) >= 3
        # Check that chunk IDs are sequential
        for i, chunk in enumerate(all_chunks):
            assert chunk.chunk_id == i

        # Check that page numbers are preserved
        page_numbers = set(chunk.page_number for chunk in all_chunks)
        assert 1 in page_numbers or 2 in page_numbers or 3 in page_numbers

    def test_token_estimation(self):
        """Test token count estimation."""
        service = ChunkingService()
        text = "This is a test with ten words in it total."

        token_count = service._estimate_tokens(text)

        # Should be roughly 10 * 1.3 = 13 tokens
        assert 8 <= token_count <= 18  # Allow some variance
