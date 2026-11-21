"""Vector store abstraction using ChromaDB."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector storage and similarity search via ChromaDB."""

    def __init__(self, persist_directory: Optional[Path] = None):
        """Initialize vector store service.

        Args:
            persist_directory: Directory for ChromaDB persistence. Defaults to settings.
        """
        self.persist_directory = persist_directory or Path("./storage/chroma_data")
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        try:
            self._client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name="document_chunks",
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise RuntimeError(f"Vector store initialization failed: {str(e)}")

    def add_chunks(
        self,
        document_id: str,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[dict],
    ) -> None:
        """Add document chunks and embeddings to the vector store.

        Args:
            document_id: ID of the parent document
            chunk_ids: Unique IDs for each chunk
            embeddings: List of embedding vectors
            documents: List of chunk text strings
            metadatas: List of metadata dictionaries (page_number, etc.)
        """
        if not chunk_ids:
            return

        try:
            # Ensure document_id is in metadata for easy deletion
            enriched_metadatas = []
            for meta in metadatas:
                m = meta.copy()
                m["document_id"] = document_id
                enriched_metadatas.append(m)

            self._collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=enriched_metadatas,
            )
        except Exception as e:
            logger.error(f"Failed to add vectors to store: {e}")
            raise RuntimeError(f"Failed to store vectors: {str(e)}")

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        exclude_document_id: Optional[str] = None,
    ) -> List[dict]:
        """Search for nearest neighbor chunks by embedding similarity.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of nearest neighbors to return
            exclude_document_id: Optional document ID to exclude from results

        Returns:
            List of matching chunks with similarity scores and metadata
        """
        try:
            where_filter = None
            if exclude_document_id:
                where_filter = {"document_id": {"$ne": exclude_document_id}}

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            matches = []
            if results and results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    # ChromaDB returns cosine distance; similarity = 1 - distance
                    distance = results["distances"][0][i]
                    similarity = 1.0 - distance

                    matches.append(
                        {
                            "chunk_id": results["ids"][0][i],
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "similarity": float(similarity),
                        }
                    )

            return matches
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def delete_document_vectors(self, document_id: str) -> None:
        """Delete all vectors associated with a document ID.

        Args:
            document_id: ID of document to delete
        """
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception as e:
            logger.error(f"Failed to delete vectors for document {document_id}: {e}")
            raise RuntimeError(f"Failed to remove document vectors: {str(e)}")
