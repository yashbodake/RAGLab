import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """Implements embedding generation using sentence-transformers all-MiniLM-L6-v2."""

    def __init__(self):
        self.model: SentenceTransformer | None = None
        self.model_name = "all-MiniLM-L6-v2"
        self.dimensions = 384

    def load(self):
        """Load model at startup. Uses HF_HOME cache directory."""
        self.model = SentenceTransformer(self.model_name)

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts to embeddings.

        Args:
            texts: List of strings to embed.
            batch_size: Max batch size for encoding.

        Returns:
            np.ndarray of shape (len(texts), 384).
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded. Call load() first.")

        # Ensure input is a list of strings
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        
        # Ensure returned value is np.ndarray
        return np.array(embeddings)
