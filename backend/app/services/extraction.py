"""PDF and text extraction service with page-aware extraction."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.errors import FileProcessingError


@dataclass
class PageText:
    """Text extracted from a single page."""

    page_number: int  # 1-indexed
    text: str
    char_count: int


@dataclass
class ExtractionResult:
    """Result of document extraction."""

    file_path: Path
    file_type: str  # 'pdf' or 'txt'
    total_pages: int
    pages: List[PageText]
    total_chars: int
    metadata: dict


class ExtractionService:
    """Service for extracting text from PDF and TXT files."""

    def extract_pdf(self, file_path: Path) -> ExtractionResult:
        """Extract text from PDF file, preserving page numbers.

        Args:
            file_path: Path to PDF file

        Returns:
            ExtractionResult with page-by-page text

        Raises:
            FileProcessingError: If extraction fails
        """
        try:
            reader = PdfReader(str(file_path))
            pages: List[PageText] = []
            total_chars = 0

            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()

                # Clean up obvious extraction artifacts
                text = self._clean_extracted_text(text)

                char_count = len(text)
                total_chars += char_count

                pages.append(
                    PageText(page_number=page_num, text=text, char_count=char_count)
                )

            # Extract metadata
            metadata = {}
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                }

            return ExtractionResult(
                file_path=file_path,
                file_type="pdf",
                total_pages=len(pages),
                pages=pages,
                total_chars=total_chars,
                metadata=metadata,
            )

        except PdfReadError as e:
            raise FileProcessingError(f"Failed to read PDF: {str(e)}")
        except Exception as e:
            raise FileProcessingError(f"PDF extraction failed: {str(e)}")

    def extract_txt(self, file_path: Path) -> ExtractionResult:
        """Extract text from TXT file.

        Args:
            file_path: Path to TXT file

        Returns:
            ExtractionResult (treated as single page)

        Raises:
            FileProcessingError: If extraction fails
        """
        try:
            text = file_path.read_text(encoding="utf-8")

            # Clean text
            text = self._clean_extracted_text(text)

            char_count = len(text)

            pages = [PageText(page_number=1, text=text, char_count=char_count)]

            return ExtractionResult(
                file_path=file_path,
                file_type="txt",
                total_pages=1,
                pages=pages,
                total_chars=char_count,
                metadata={},
            )

        except UnicodeDecodeError:
            raise FileProcessingError(
                "Unable to decode text file. Please ensure it's UTF-8 encoded."
            )
        except Exception as e:
            raise FileProcessingError(f"Text extraction failed: {str(e)}")

    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract text from file based on extension.

        Args:
            file_path: Path to file

        Returns:
            ExtractionResult

        Raises:
            FileProcessingError: If extraction fails or file type unsupported
        """
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            return self.extract_pdf(file_path)
        elif extension == ".txt":
            return self.extract_txt(file_path)
        else:
            raise FileProcessingError(f"Unsupported file type: {extension}")

    def _clean_extracted_text(self, text: str) -> str:
        """Clean up common extraction artifacts.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove null bytes
        text = text.replace("\x00", "")

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text
