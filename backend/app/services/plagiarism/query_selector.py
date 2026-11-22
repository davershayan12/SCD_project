"""Distinctive passage query selector for web and scholarly searches."""

import re
from typing import List


class QuerySelector:
    """Service to select distinctive multi-word phrases across a document."""

    def __init__(self, phrase_words: int = 10):
        self.phrase_words = phrase_words

    def select_queries(self, text: str, max_queries: int = 15) -> List[str]:
        """Extract distinctive contiguous phrase queries from document text."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        queries = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            words = sentence.split()
            if len(words) >= self.phrase_words:
                # Take windows of phrase_words
                for i in range(0, len(words) - self.phrase_words + 1, max(1, self.phrase_words // 2)):
                    phrase = " ".join(words[i : i + self.phrase_words])
                    queries.append(phrase)
                    if len(queries) >= max_queries:
                        return queries

        return queries
