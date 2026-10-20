"""
Embedding Service for Lexora Legal Intelligence.
Uses SentenceTransformers with lazy model loading to ensure fast, non-blocking imports.
"""
from typing import List, Optional

_model = None

def get_model():
    """Lazily load SentenceTransformer model on first usage."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_embedding(text: str) -> List[float]:
    """Generates embedding for a given text."""
    model_instance = get_model()
    embedding = model_instance.encode(text)
    return embedding.tolist()

class _LazyModelProxy:
    """Proxy object so legacy `model.encode(...)` calls still work seamlessly."""
    def __getattr__(self, name):
        return getattr(get_model(), name)

    def encode(self, *args, **kwargs):
        return get_model().encode(*args, **kwargs)

model = _LazyModelProxy()
