"""Security utilities for file validation."""

import hashlib
import mimetypes
import secrets
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.config import settings
from app.core.errors import ValidationError


ALLOWED_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
}


def validate_file_extension(filename: str) -> None:
    """Validate file extension.

    Args:
        filename: Original filename from upload

    Raises:
        ValidationError: If extension is not allowed
    """
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{extension}' not supported. "
            f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def validate_file_size(file_size: int) -> None:
    """Validate file size.

    Args:
        file_size: File size in bytes

    Raises:
        ValidationError: If file is too large
    """
    if file_size > settings.max_file_size_bytes:
        raise ValidationError(
            f"File size ({file_size / 1024 / 1024:.1f} MB) exceeds "
            f"maximum allowed size ({settings.max_file_size_mb} MB)"
        )


def validate_mime_type(file_path: Path) -> str:
    """Validate MIME type of file.

    Args:
        file_path: Path to file

    Returns:
        Detected MIME type

    Raises:
        ValidationError: If MIME type is not allowed
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))

    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"File type '{mime_type}' not supported. "
            f"Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    return mime_type


def validate_pdf_content(file_path: Path) -> int:
    """Validate PDF can be opened and check page count.

    Args:
        file_path: Path to PDF file

    Returns:
        Number of pages

    Raises:
        ValidationError: If PDF is corrupt, encrypted, or has too many pages
    """
    try:
        reader = PdfReader(str(file_path))

        # Check if encrypted
        if reader.is_encrypted:
            raise ValidationError(
                "Encrypted PDFs are not supported. "
                "Please upload an unencrypted version."
            )

        # Check page count
        page_count = len(reader.pages)
        if page_count == 0:
            raise ValidationError("PDF file contains no pages")

        if page_count > settings.max_page_count:
            raise ValidationError(
                f"PDF has {page_count} pages, exceeding maximum "
                f"allowed ({settings.max_page_count} pages)"
            )

        # Try to extract text from first page to verify it's not scanned
        first_page = reader.pages[0]
        text = first_page.extract_text()

        if not text or len(text.strip()) < 10:
            raise ValidationError(
                "PDF appears to be scanned or contains no extractable text. "
                "OCR is not supported yet. Please upload a text-based PDF."
            )

        return page_count

    except PdfReadError as e:
        raise ValidationError(f"Corrupt or invalid PDF file: {str(e)}")
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Failed to read PDF file: {str(e)}")


def compute_file_hash(file_obj: BinaryIO) -> str:
    """Compute SHA-256 hash of file content.

    Args:
        file_obj: File-like object (must be seekable)

    Returns:
        Hex digest of SHA-256 hash
    """
    file_obj.seek(0)
    file_hash = hashlib.sha256()

    while chunk := file_obj.read(8192):
        file_hash.update(chunk)

    file_obj.seek(0)
    return file_hash.hexdigest()


def generate_random_filename(extension: str) -> str:
    """Generate a random filename with given extension.

    Args:
        extension: File extension (including dot, e.g., '.pdf')

    Returns:
        Random filename like 'a3f7b2e9d4c1.pdf'
    """
    random_name = secrets.token_hex(16)
    return f"{random_name}{extension}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename (only extension is preserved)
    """
    extension = Path(filename).suffix.lower()
    return generate_random_filename(extension)
