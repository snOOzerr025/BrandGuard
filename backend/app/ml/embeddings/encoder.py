"""
ml/embeddings/encoder.py
-------------------------
Sentence-level embedding encoder using sentence-transformers.

Model: all-MiniLM-L6-v2
  - 80MB, fast on CPU (~2000 sentences/sec)
  - 384-dimensional embeddings
  - Strong performance on semantic similarity tasks

Used for:
  1. Embedding the full review corpus for pgvector storage (Phase 3/4)
  2. KMeans/HDBSCAN clustering for theme discovery (cluster.py)
"""
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


class ReviewEncoder:
    """
    Encodes review texts into 384-dim semantic embeddings.

    Usage:
        encoder = ReviewEncoder()
        embeddings = encoder.encode(["Great battery life!", "Broke in a week."])
        # numpy array of shape (2, 384)
    """

    def __init__(self):
        self._model = SentenceTransformer(MODEL_NAME)

    def encode(
        self,
        texts: list[str],
        batch_size: int = 64,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode a list of texts into L2-normalized sentence embeddings.

        Args:
            texts: List of review strings.
            batch_size: Number of texts to encode per forward pass.
            show_progress: Show tqdm progress bar for large batches.

        Returns:
            numpy ndarray of shape (len(texts), 384), dtype float32.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,  # L2 normalize → cosine similarity = dot product
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def encode_one(self, text: str) -> np.ndarray:
        """Encode a single text. Returns shape (384,)."""
        return self.encode([text])[0]
