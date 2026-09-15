from backend.config import settings
from backend.services.vector_service import search_semantic
from backend.services.bm25_service import bm25_service
from backend.services.reranker_service import rerank_results

class SearchService:
    def __init__(self):
        self.semantic_weight = settings.SEMANTIC_WEIGHT
        self.keyword_weight = settings.KEYWORD_WEIGHT

    def hybrid_search(self, query: str, top_k: int = 10, filters: dict = None):
        """
        Executes semantic and BM25 searches, dedups, and applies weighted scoring.
        """
        if not query:
            return []

        # Retrieve more items initially to allow for reranking pruning
        initial_k = top_k * 2

        semantic_results = search_semantic(query, n_results=initial_k, filters=filters)
        keyword_results = bm25_service.search(query, top_k=initial_k, filters=filters)

        # Normalization helpers
        def normalize_scores(results):
            if not results:
                return results
            max_score = max(results, key=lambda x: x["score"])["score"]
            if max_score > 0:
                for r in results:
                    r["score"] = r["score"] / max_score
            return results

        semantic_results = normalize_scores(semantic_results)
        keyword_results = normalize_scores(keyword_results)

        # Deduplication and merging
        merged_results = {}

        for res in semantic_results:
            merged_results[res["id"]] = {
                "id": res["id"],
                "metadata": res["metadata"],
                "text": res["text"],
                "semantic_score": res["score"],
                "keyword_score": 0.0
            }

        for res in keyword_results:
            if res["id"] in merged_results:
                merged_results[res["id"]]["keyword_score"] = res["score"]
            else:
                merged_results[res["id"]] = {
                    "id": res["id"],
                    "metadata": res["metadata"],
                    "text": res["text"],
                    "semantic_score": 0.0,
                    "keyword_score": res["score"]
                }

        # Calculate final hybrid score
        for doc_id, doc in merged_results.items():
            doc["score"] = (doc["semantic_score"] * self.semantic_weight) + (doc["keyword_score"] * self.keyword_weight)

        docs = list(merged_results.values())
        
        # Sort by initial hybrid score before reranking
        docs.sort(key=lambda x: x["score"], reverse=True)

        # Rerank with Gemini to get Research Relevance Score and Explanations
        reranked_docs = rerank_results(query, docs, top_k=top_k)

        # Format output
        formatted_results = []
        for doc in reranked_docs:
            formatted_results.append({
                "chunk_id": doc["id"],
                "document_id": doc["metadata"].get("document_id"),
                "case_name": doc["metadata"].get("case_name", "Unknown Case"),
                "court": doc["metadata"].get("court", "Unknown Court"),
                "year": doc["metadata"].get("year", 0),
                "page_number": doc["metadata"].get("page_number", 1),
                "relevance_score": doc.get("relevance_score", 0.0),
                "semantic_score": doc["semantic_score"],
                "keyword_score": doc["keyword_score"],
                "matched_text": doc["text"],
                "reason": doc.get("reason", "Retrieved by hybrid search.")
            })

        return formatted_results

search_service = SearchService()
