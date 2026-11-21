"""Unit tests for semantic embeddings and vector store."""

import tempfile
from pathlib import Path
import pytest

from app.services.semantic.embeddings import EmbeddingService
from app.services.semantic.vector_store import VectorStoreService


class TestEmbeddingService:
    """Test embedding generation."""

    def test_embedding_service_init(self):
        """Test embedding service initialization."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        assert service.model_name == "all-MiniLM-L6-v2"
        assert service.device == "cpu"


class TestVectorStoreService:
    """Test vector store operations."""

    def test_vector_store_operations(self, tmp_path):
        """Test adding and searching vectors in ChromaDB."""
        # Use temp directory for vector store
        store = VectorStoreService(persist_directory=tmp_path / "chroma")

        # Add chunks
        document_id = "doc-123"
        chunk_ids = ["chunk-1", "chunk-2"]
        # Dummy 384-dimensional embeddings (MiniLM size)
        embeddings = [[0.1] * 384, [0.2] * 384]
        documents = ["This is test text one.", "This is test text two."]
        metadatas = [{"page_number": 1, "chunk_index": 0}, {"page_number": 1, "chunk_index": 1}]

        store.add_chunks(document_id, chunk_ids, embeddings, documents, metadatas)

        # Search
        results = store.search(query_embedding=[0.1] * 384, n_results=2)
        assert len(results) > 0

        # Delete document vectors
        store.delete_document_vectors(document_id)

        # Search again after deletion
        results_after = store.search(query_embedding=[0.1] * 384, n_results=2)
        # Should not find deleted chunks from doc-123
        for res in results_after:
            assert res["metadata"]["document_id"] != document_id
