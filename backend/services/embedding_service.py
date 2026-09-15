from sentence_transformers import SentenceTransformer

# Load a local model, e.g., an all-MiniLM model for fast, good semantic search
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str) -> list[float]:
    """Generates embedding for a given text."""
    embedding = model.encode(text)
    return embedding.tolist()
