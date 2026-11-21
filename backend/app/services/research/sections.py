"""Section detection service for academic papers using heuristics and headings."""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PaperSection:
    """A detected section of an academic paper."""

    section_type: str  # abstract, introduction, methodology, results, discussion, limitations, conclusion, references, other
    title: str
    page_number: int
    text: str


class SectionDetectionService:
    """Service for detecting standard academic sections in extracted text."""

    SECTION_PATTERNS = {
        "abstract": r"\babstract\b",
        "introduction": r"\b(1\.\s*)?introduction\b",
        "methodology": r"\b(2\.\s*)?(methodology|methods|approach|model|framework)\b",
        "results": r"\b(3\.\s*)?(results|experiments|evaluation|performance)\b",
        "discussion": r"\b(4\.\s*)?(discussion|analysis)\b",
        "limitations": r"\b(limitations?|threats to validity)\b",
        "conclusion": r"\b(5\.\s*)?(conclusion|future work|summary)\b",
        "references": r"\b(references|bibliography)\b",
    }

    def detect_sections(self, pages: List[tuple[str, int]]) -> List[PaperSection]:
        """Detect sections across document pages.

        Args:
            pages: List of (page_text, page_number) tuples

        Returns:
            List of detected PaperSection objects
        """
        sections: List[PaperSection] = []

        # Default section if none detected
        current_type = "introduction"
        current_title = "Document Start"
        current_page = 1
        current_text_lines = []

        for text, page_num in pages:
            lines = text.split("\n")
            for line in lines:
                line_lower = line.strip().lower()

                # Check if line looks like a section heading
                detected_type = self._match_heading(line_lower)
                if detected_type and len(line.strip()) < 80:
                    # Save previous section if not empty
                    if current_text_lines:
                        sections.append(
                            PaperSection(
                                section_type=current_type,
                                title=current_title,
                                page_number=current_page,
                                text="\n".join(current_text_lines),
                            )
                        )
                        current_text_lines = []

                    current_type = detected_type
                    current_title = line.strip()
                    current_page = page_num
                else:
                    current_text_lines.append(line)

            # End of page
            if current_text_lines:
                sections.append(
                    PaperSection(
                        section_type=current_type,
                        title=current_title,
                        page_number=current_page,
                        text="\n".join(current_text_lines),
                    )
                )
                current_text_lines = []

        return sections

    def _match_heading(self, line: str) -> Optional[str]:
        """Match line against known section heading patterns."""
        for section_type, pattern in self.SECTION_PATTERNS.items():
            if re.search(pattern, line):
                return section_type
        return None
