"""Unit tests for winnowing fingerprinting service."""

import pytest

from app.services.plagiarism.winnowing import WinnowingService


class TestWinnowingService:
    """Test winnowing fingerprinting."""

    def test_tokenize(self):
        """Test text tokenization."""
        service = WinnowingService()
        text = "This is a test document."

        tokens = service.tokenize(text)

        assert tokens == ["this", "is", "a", "test", "document."]
        assert all(t.islower() for t in tokens)

    def test_tokenize_empty(self):
        """Test empty text tokenization."""
        service = WinnowingService()
        tokens = service.tokenize("")

        assert tokens == []

    def test_create_shingles(self):
        """Test k-gram shingle creation."""
        service = WinnowingService(k=3)
        tokens = ["the", "quick", "brown", "fox", "jumps"]

        shingles = service.create_shingles(tokens)

        assert len(shingles) == 3  # 5 - 3 + 1
        assert shingles[0] == ("the quick brown", 0)
        assert shingles[1] == ("quick brown fox", 1)
        assert shingles[2] == ("brown fox jumps", 2)

    def test_create_shingles_too_short(self):
        """Test shingle creation with text shorter than k."""
        service = WinnowingService(k=5)
        tokens = ["too", "short"]

        shingles = service.create_shingles(tokens)

        assert shingles == []

    def test_hash_shingle_consistency(self):
        """Test that same shingle produces same hash."""
        service = WinnowingService()
        shingle = "the quick brown"

        hash1 = service.hash_shingle(shingle)
        hash2 = service.hash_shingle(shingle)

        assert hash1 == hash2
        assert isinstance(hash1, int)

    def test_hash_shingle_different(self):
        """Test that different shingles produce different hashes."""
        service = WinnowingService()

        hash1 = service.hash_shingle("the quick brown")
        hash2 = service.hash_shingle("quick brown fox")

        assert hash1 != hash2

    def test_winnowing_guarantee(self):
        """Test winnowing guarantees to detect matches of length >= w+k-1."""
        service = WinnowingService(k=5, w=4)
        text = "the quick brown fox jumps over the lazy dog"

        result = service.fingerprint(text)

        # Should have fingerprints
        assert len(result.fingerprints) > 0
        assert result.k == 5
        assert result.w == 4

        # Guarantees detection of >= 5+4-1 = 8 token matches

    def test_fingerprint_empty_text(self):
        """Test fingerprinting empty text."""
        service = WinnowingService()
        result = service.fingerprint("")

        assert len(result.fingerprints) == 0
        assert result.total_tokens == 0
        assert result.total_shingles == 0

    def test_fingerprint_short_text(self):
        """Test fingerprinting text shorter than k."""
        service = WinnowingService(k=5)
        text = "too short"

        result = service.fingerprint(text)

        assert len(result.fingerprints) == 0
        assert result.total_tokens == 2

    def test_fingerprint_document_multipage(self):
        """Test fingerprinting multi-page document."""
        service = WinnowingService(k=3, w=2)
        pages = [
            ("This is page one with some text.", 1),
            ("This is page two with more text.", 2),
            ("This is page three final page.", 3),
        ]

        result, position_to_page = service.fingerprint_document(pages)

        assert len(result.fingerprints) > 0
        assert len(position_to_page) > 0

        # Check page mapping
        assert 1 in position_to_page.values()
        assert 2 in position_to_page.values()
        assert 3 in position_to_page.values()

    def test_fingerprint_document_single_page(self):
        """Test fingerprinting single-page document."""
        service = WinnowingService(k=3, w=2)
        pages = [("This is a single page document.", 1)]

        result, position_to_page = service.fingerprint_document(pages)

        assert len(result.fingerprints) > 0
        assert all(p == 1 for p in position_to_page.values())

    def test_identical_text_identical_fingerprints(self):
        """Test that identical text produces identical fingerprints."""
        service = WinnowingService(k=5, w=4)
        text = "The quick brown fox jumps over the lazy dog"

        result1 = service.fingerprint(text)
        result2 = service.fingerprint(text)

        # Should have same fingerprints
        fp1_hashes = {fp.hash_value for fp in result1.fingerprints}
        fp2_hashes = {fp.hash_value for fp in result2.fingerprints}

        assert fp1_hashes == fp2_hashes

    def test_minor_change_different_fingerprints(self):
        """Test that minor changes produce different fingerprints."""
        service = WinnowingService(k=5, w=4)
        text1 = "The quick brown fox jumps over the lazy dog"
        text2 = "The quick brown cat jumps over the lazy dog"

        result1 = service.fingerprint(text1)
        result2 = service.fingerprint(text2)

        # Should have some different fingerprints
        fp1_hashes = {fp.hash_value for fp in result1.fingerprints}
        fp2_hashes = {fp.hash_value for fp in result2.fingerprints}

        assert fp1_hashes != fp2_hashes

    def test_fingerprint_positions(self):
        """Test that fingerprint positions are correct."""
        service = WinnowingService(k=3, w=2)
        text = "one two three four five"

        result = service.fingerprint(text)

        # All positions should be valid
        for fp in result.fingerprints:
            assert 0 <= fp.position < result.total_tokens - service.k + 1
            assert isinstance(fp.text, str)
