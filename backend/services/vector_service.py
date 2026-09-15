import os
import logging
import chromadb
from chromadb.config import Settings
from backend.services.embedding_service import get_embedding
from backend.services.bm25_service import bm25_service

logger = logging.getLogger("lexora.vector_service")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="legal_documents")


def index_document_chunk(
    chunk_id: str,
    case_id: int,
    document_id: int,
    page_number: int,
    text: str,
    case_name: str,
    court: str,
    year: int,
    category: str = "",
    legal_topics: str = "",
    # Phase 10 additions
    section: str = "",
    chunk_sequence: int = 0,
):
    """
    Index a document chunk into the vector store and BM25 index.
    Metadata supports filtering by case_id, document_id, court, year,
    section, legal_topics, and page_number for hybrid search.
    """
    embedding = get_embedding(text)

    metadata = {
        "case_id": case_id,
        "document_id": document_id,
        "page_number": page_number,
        "case_name": case_name,
        "court": court,
        "year": year,
        "chunk_sequence": chunk_sequence,
    }

    if category:
        metadata["category"] = category
    if legal_topics:
        metadata["legal_topics"] = legal_topics
    # Phase 10: section metadata enables filtering by legal document section
    if section:
        metadata["section"] = section

    # Index in ChromaDB (Semantic)
    collection.add(
        ids=[chunk_id],
        embeddings=[embedding],
        metadatas=[metadata],
        documents=[text]
    )

    # Index in BM25 (Lexical)
    bm25_service.index_chunk(chunk_id, text, metadata)


def chunk_exists(chunk_id: str) -> bool:
    """
    Check if a chunk is already indexed.
    Used for idempotent retry — avoids duplicate embeddings.
    """
    try:
        result = collection.get(ids=[chunk_id])
        return bool(result and result.get("ids"))
    except Exception:
        return False


def delete_document_chunks(document_id: int) -> int:
    """
    Remove all indexed chunks for a document.
    Used during document deletion and idempotent retry (clear before re-index).
    Returns count of deleted chunks.
    """
    try:
        # Get all chunk IDs for this document
        results = collection.get(
            where={"document_id": document_id}
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            # Also remove from BM25
            for chunk_id in ids_to_delete:
                bm25_service.remove_chunk(chunk_id)
            logger.info("Deleted %d chunks for document_id=%d", len(ids_to_delete), document_id)
        return len(ids_to_delete)
    except Exception as e:
        logger.error("Error deleting chunks for document %d: %s", document_id, str(e))
        return 0


def search_semantic(query: str, n_results: int = 10, filters: dict = None):
    query_embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=filters
    )

    parsed_results = []
    if results["ids"] and len(results["ids"]) > 0:
        for i in range(len(results["ids"][0])):
            parsed_results.append({
                "id": results["ids"][0][i],
                "score": 1.0 - (results["distances"][0][i] if "distances" in results and results["distances"] else 0.0),
                "metadata": results["metadatas"][0][i],
                "text": results["documents"][0][i],
                "source": "semantic"
            })
    return parsed_results


def search_in_document(document_id: int, query: str, n_results: int = 10) -> list:
    """
    Search within a single document by document_id filter.
    Used for the source viewer in-document search feature.
    """
    query_embedding = get_embedding(query)
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"document_id": document_id}
        )
        parsed = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i]
                parsed.append({
                    "id": results["ids"][0][i],
                    "page_number": meta.get("page_number", 0),
                    "section": meta.get("section", "OTHER"),
                    "score": 1.0 - (results["distances"][0][i] if "distances" in results else 0.0),
                    "text": results["documents"][0][i],
                })
        return parsed
    except Exception as e:
        logger.error("search_in_document failed for doc %d: %s", document_id, str(e))
        return []
