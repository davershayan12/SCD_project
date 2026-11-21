"""Unit tests for text normalization service."""

import pytest

from app.services.normalization import NormalizationService


class TestNormalizationService:
    """Test text normalization."""

    def test_unicode_normalization(self):
        """Test Unicode NFKC normalization."""
        service = NormalizationService()
        text = "Ĥellö Wörld"  # With diacritics
        result = service.normalize(text, page_number=1)

        assert result.text is not None
        assert result.page_number == 1
        assert len(result.mappings) > 0

    def test_ligature_replacement(self):
        """Test ligature expansion."""
        service = NormalizationService()
        text = "The ﬁle contains ﬂow charts."
        result = service.normalize(text, page_number=1)

        assert "fi" in result.text
        assert "fl" in result.text
        assert "ﬁ" not in result.text
        assert "ﬂ" not in result.text

    def test_dehyphenation(self):
        """Test removal of line-break hyphens."""
        service = NormalizationService()
        text = "This is a docu-\nment with hyphenation."
        result = service.normalize(text, page_number=1, dehyphenate=True)

        assert "docu-\nm" not in result.text
        assert "document" in result.text

    def test_dehyphenation_preserved_with_capital(self):
        """Test that hyphens before capitals are preserved."""
        service = NormalizationService()
        text = "End of sentence-\nNew sentence starts."
        result = service.normalize(text, page_number=1, dehyphenate=True)

        # Should preserve hyphen before capital letter
        assert "sentence-" in result.text or "sentence " in result.text

    def test_whitespace_collapse(self):
        """Test collapsing of excessive whitespace."""
        service = NormalizationService()
        text = "Multiple    spaces   and\n\n\n\nmany newlines."
        result = service.normalize(text, page_number=1)

        assert "    " not in result.text  # Multiple spaces collapsed
        assert "\n\n\n" not in result.text  # Multiple newlines collapsed

    def test_punctuation_spacing(self):
        """Test punctuation spacing cleanup."""
        service = NormalizationService()
        text = "Hello , world .This is wrong."
        result = service.normalize(text, page_number=1)

        assert " ," not in result.text
        assert " ." not in result.text
        assert ".T" not in result.text  # Space added after period

    def test_empty_text(self):
        """Test handling of empty text."""
        service = NormalizationService()
        result = service.normalize("", page_number=1)

        assert result.text == ""
        assert result.page_number == 1

    def test_batch_normalization(self):
        """Test batch normalization of multiple texts."""
        service = NormalizationService()
        texts = [
            ("First page with ﬁle", 1),
            ("Second page with ﬂow", 2),
            ("Third page", 3),
        ]

        results = service.normalize_batch(texts)

        assert len(results) == 3
        assert results[0].page_number == 1
        assert results[1].page_number == 2
        assert results[2].page_number == 3
        assert "fi" in results[0].text
        assert "fl" in results[1].text
