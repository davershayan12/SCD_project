"""Embedding generation service using Sentence Transformers."""

import logging
from typing import List, Optional
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Sentence Transformers."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
    ):
        """Initialize embedding service.

        Args:
            model_name: Sentence transformer model name (Apache-2.0)
            device: Computing device ('cpu' or 'cuda'). Defaults to settings.
        """
        self.model_name = model_name
        self.device = device or settings.embedding_device
        self._model = None

    @property
    def model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model '{self.model_name}' on device '{self.device}'...")
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except Exception as e:
                logger.error(f"Failed to load embedding model '{self.model_name}': {e}")
                raise RuntimeError(
                    f"Failed to load embedding model '{self.model_name}': {str(e)}. "
                    "Ensure internet connection for initial download or check model name."
                )
        return self._model

    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings
            batch_size: Batch size for encoding

        Returns:
            List of embedding vectors (floats)
        """
        if not texts:
            return []

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Embedding generation failed: {str(e)}")

    def encode_single(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        results = self.encode([text], batch_size=1)
        return results[0] if results else []
