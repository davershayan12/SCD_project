"""Unit tests for file security validation."""

import tempfile
from pathlib import Path

import pytest

from app.core.errors import ValidationError
from app.core.security import (
    compute_file_hash,
    generate_random_filename,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
    validate_pdf_content,
)


class TestFileValidation:
    """Test file validation functions."""

    def test_validate_allowed_extensions(self):
        """Test that allowed extensions pass validation."""
        validate_file_extension("document.pdf")
        validate_file_extension("text.txt")
        validate_file_extension("FILE.PDF")  # Case insensitive

    def test_validate_disallowed_extensions(self):
        """Test that disallowed extensions raise errors."""
        with pytest.raises(ValidationError, match="not supported"):
            validate_file_extension("document.docx")

        with pytest.raises(ValidationError, match="not supported"):
            validate_file_extension("image.jpg")

    def test_validate_file_size_ok(self):
        """Test file size validation passes for allowed sizes."""
        validate_file_size(1024)  # 1 KB
        validate_file_size(10 * 1024 * 1024)  # 10 MB

    def test_validate_file_size_too_large(self):
        """Test file size validation fails for oversized files."""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_file_size(100 * 1024 * 1024)  # 100 MB (default max is 50)

    def test_validate_mime_type_pdf(self, tmp_path):
        """Test MIME type validation for PDF."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mime_type = validate_mime_type(pdf_file)
        assert mime_type == "application/pdf"

    def test_validate_mime_type_txt(self, tmp_path):
        """Test MIME type validation for TXT."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content")

        mime_type = validate_mime_type(txt_file)
        assert mime_type == "text/plain"

    def test_validate_mime_type_invalid(self, tmp_path):
        """Test MIME type validation fails for unsupported types."""
        jpg_file = tmp_path / "test.jpg"
        jpg_file.write_bytes(b"\xff\xd8\xff")

        with pytest.raises(ValidationError, match="not supported"):
            validate_mime_type(jpg_file)

    def test_compute_file_hash(self):
        """Test file hash computation."""
        from io import BytesIO

        content = b"Test content for hashing"
        file_obj = BytesIO(content)

        hash1 = compute_file_hash(file_obj)
        file_obj.seek(0)
        hash2 = compute_file_hash(file_obj)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_compute_file_hash_different_content(self):
        """Test that different content produces different hashes."""
        from io import BytesIO

        hash1 = compute_file_hash(BytesIO(b"Content A"))
        hash2 = compute_file_hash(BytesIO(b"Content B"))

        assert hash1 != hash2

    def test_generate_random_filename(self):
        """Test random filename generation."""
        filename1 = generate_random_filename(".pdf")
        filename2 = generate_random_filename(".pdf")

        assert filename1.endswith(".pdf")
        assert filename2.endswith(".pdf")
        assert filename1 != filename2
        assert len(filename1) > 10

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        original = "../../../etc/passwd.pdf"
        sanitized = sanitize_filename(original)

        assert sanitized.endswith(".pdf")
        assert ".." not in sanitized
        assert "/" not in sanitized
        assert "\\" not in sanitized

    def test_validate_pdf_content_valid(self, sample_pdf_content, tmp_path):
        """Test PDF content validation with valid PDF."""
        pdf_file = tmp_path / "valid.pdf"
        pdf_file.write_bytes(sample_pdf_content)

        page_count = validate_pdf_content(pdf_file)
        assert page_count == 1

    def test_validate_pdf_content_corrupt(self, tmp_path):
        """Test PDF content validation with corrupt PDF."""
        pdf_file = tmp_path / "corrupt.pdf"
        pdf_file.write_bytes(b"Not a real PDF")

        with pytest.raises(ValidationError, match="Corrupt or invalid"):
            validate_pdf_content(pdf_file)

    def test_validate_pdf_content_empty(self, tmp_path):
        """Test PDF validation with no extractable text."""
        # Create a PDF with no text
        minimal_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
165
%%EOF"""

        pdf_file = tmp_path / "empty.pdf"
        pdf_file.write_bytes(minimal_pdf)

        with pytest.raises(ValidationError, match="scanned or contains no extractable text"):
            validate_pdf_content(pdf_file)
