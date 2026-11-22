"""Document and HTML cleaning utilities for accurate plagiarism and AI detection."""

import re
from bs4 import BeautifulSoup


class DocumentCleaner:
    """Cleans HTML pages and extracts clean body prose."""

    @staticmethod
    def clean_html(html_content: str) -> str:
        """Extract clean text from HTML, stripping scripts, styles, navs and footers."""
        try:
            soup = BeautifulSoup(html_content, "lxml")

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                element.decompose()

            text = soup.get_text(separator=" ")

            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception:
            # Fallback regex strip
            text = re.sub(r"<[^>]+>", " ", html_content)
            return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def strip_references(text: str) -> str:
        """Strip references/bibliography section if present."""
        patterns = [
            r"\b(references|bibliography|works cited)\b.*$",
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if match:
                text = text[:match.start()]
        return text.strip()
