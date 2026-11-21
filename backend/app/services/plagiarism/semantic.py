"""Semantic similarity service for detecting possible paraphrases using embeddings."""

from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import Session

from app.services.semantic.embeddings import EmbeddingService
from app.services.semantic.vector_store import VectorStoreService


@dataclass
class SemanticCandidate:
    """A semantic similarity candidate (possible paraphrase)."""

    source_document_id: str
    source_title: str
    source_page: int
    similarity: float
    submitted_text: str
    source_text: str
    match_type: str = "possible-paraphrase"


class SemanticMatchingService:
    """Service for semantic candidate retrieval and re-ranking."""

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        max_candidates: int = 10,
    ):
        """Initialize semantic matching service.

        Args:
            similarity_threshold: Cosine similarity threshold for possible paraphrases.
                                  Tuned on validation sets; default 0.75.
            max_candidates: Maximum number of semantic candidates to return.
        """
        self.similarity_threshold = similarity_threshold
        self.max_candidates = max_candidates
        self.embeddings = EmbeddingService()
        self.vector_store = VectorStoreService()

    def index_document_chunks(
        self, document_id: str, chunks: List[dict]
    ) -> None:
        """Embed and index document chunks into the vector store.

        Args:
            document_id: Document ID
            chunks: List of chunk dictionaries (id, text, page_number)
        """
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]
        chunk_ids = [f"{document_id}_chunk_{chunk['chunk_index']}" for chunk in chunks]
        metadatas = [
            {
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
            }
            for chunk in chunks
        ]

        # Generate embeddings in batches
        embeddings = self.embeddings.encode(texts)

        # Store in vector store
        self.vector_store.add_chunks(
            document_id=document_id,
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def find_semantic_candidates(
        self,
        document_id: str,
        submitted_chunks: List[dict],
        source_titles: dict,
    ) -> List[SemanticCandidate]:
        """Find semantic candidates (possible paraphrases) for submitted chunks.

        Args:
            document_id: Submitted document ID
            submitted_chunks: List of submitted chunks
            source_titles: Mapping of document_id -> title

        Returns:
            List of SemanticCandidate objects
        """
        if not submitted_chunks:
            return []

        candidates = []
        seen_snippets = set()

        # Sample or check chunks (for efficiency, check representative chunks)
        for chunk in submitted_chunks:
            text = chunk["text"]
            if len(text.split()) < 10:
                continue  # Skip very short chunks

            # Generate query embedding
            query_embedding = self.embeddings.encode_single(text)

            # Search vector store, excluding same document
            results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=3,
                exclude_document_id=document_id,
            )

            for res in results:
                similarity = res["similarity"]
                if similarity >= self.similarity_threshold:
                    meta = res["metadata"]
                    source_doc_id = meta.get("document_id")
                    source_page = meta.get("page_number", 1)
                    source_text = res["text"]

                    # Avoid duplicate snippets
                    snippet_key = (source_doc_id, source_page, source_text[:50])
                    if snippet_key in seen_snippets:
                        continue
                    seen_snippets.add(snippet_key)

                    candidates.append(
                        SemanticCandidate(
                            source_document_id=source_doc_id,
                            source_title=source_titles.get(source_doc_id, "Unknown"),
                            source_page=source_page,
                            similarity=float(similarity),
                            submitted_text=text,
                            source_text=source_text,
                        )
                    )

        # Sort by similarity descending and cap at max_candidates
        candidates.sort(key=lambda c: c.similarity, reverse=True)
        return candidates[: self.max_candidates]
