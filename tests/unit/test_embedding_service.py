import pytest
import numpy as np
from backend.services.embedding import EmbeddingService

@pytest.mark.unit
def test_encode_without_load_raises():
    """Calling encode before load raises RuntimeError."""
    svc = EmbeddingService()
    with pytest.raises(RuntimeError) as exc_info:
        svc.encode(["test"])
    assert "Embedding model not loaded. Call load() first." in str(exc_info.value)

@pytest.mark.unit
def test_encode_single_text(embedding_service):
    """Single text returns shape (1, 384)."""
    emb = embedding_service.encode(["This is a test document."])
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (1, 384)

@pytest.mark.unit
def test_encode_batch(embedding_service):
    """Batch of N texts returns shape (N, 384)."""
    texts = ["Document one.", "Document two.", "Document three."]
    emb = embedding_service.encode(texts)
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (3, 384)

@pytest.mark.unit
def test_encode_normalized(embedding_service):
    """Output vectors have unit L2 norm."""
    emb = embedding_service.encode(["Check normalizations."])
    norm = np.linalg.norm(emb[0])
    assert pytest.approx(norm, abs=1e-5) == 1.0

@pytest.mark.unit
def test_encode_deterministic(embedding_service):
    """Same text produces same embedding."""
    text = "The quick brown fox jumps over the lazy dog."
    emb1 = embedding_service.encode([text])
    emb2 = embedding_service.encode([text])
    np.testing.assert_allclose(emb1, emb2, rtol=1e-5, atol=1e-8)
