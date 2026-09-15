import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.services.search_service import search_service

client = TestClient(app)

def test_search_empty_query_api():
    response = client.post("/api/search", json={"query": ""})
    assert response.status_code == 400

def test_search_no_results(monkeypatch):
    def mock_semantic(*args, **kwargs): return []
    def mock_bm25(*args, **kwargs): return []
    
    monkeypatch.setattr("backend.services.search_service.search_semantic", mock_semantic)
    monkeypatch.setattr("backend.services.search_service.bm25_service.search", mock_bm25)
    
    response = client.post("/api/search", json={"query": "completely random query"})
    assert response.status_code == 200
    assert response.json() == []

def test_hybrid_retrieval_deduplication(monkeypatch):
    mock_semantic_results = [
        {"id": "chunk_1", "score": 0.8, "metadata": {"case_name": "Case A"}, "text": "Text A", "source": "semantic"}
    ]
    mock_bm25_results = [
        {"id": "chunk_1", "score": 10.5, "metadata": {"case_name": "Case A"}, "text": "Text A", "source": "keyword"},
        {"id": "chunk_2", "score": 5.2, "metadata": {"case_name": "Case B"}, "text": "Text B", "source": "keyword"}
    ]
    def mock_semantic(*args, **kwargs): return mock_semantic_results
    def mock_bm25(*args, **kwargs): return mock_bm25_results
    def mock_rerank(query, docs, top_k):
        # Just return docs to skip Gemini call during unit test
        for doc in docs:
            doc["relevance_score"] = doc["score"] * 100
            doc["reason"] = "Mock reason"
        return sorted(docs, key=lambda x: x["relevance_score"], reverse=True)[:top_k]

    monkeypatch.setattr("backend.services.search_service.search_semantic", mock_semantic)
    monkeypatch.setattr("backend.services.search_service.bm25_service.search", mock_bm25)
    monkeypatch.setattr("backend.services.search_service.rerank_results", mock_rerank)
    
    results = search_service.hybrid_search("test", top_k=5)
    assert len(results) == 2
    
    # chunk_1 should be merged
    chunk_1 = next(r for r in results if r["matched_text"] == "Text A")
    assert chunk_1["semantic_score"] > 0
    assert chunk_1["keyword_score"] > 0
    
    # chunk_2 should only have keyword score
    chunk_2 = next(r for r in results if r["matched_text"] == "Text B")
    assert chunk_2["semantic_score"] == 0.0
    assert chunk_2["keyword_score"] > 0

def test_search_with_filters_api(monkeypatch):
    def mock_semantic(query, n_results, filters): 
        assert filters == {"court": "Supreme Court"}
        return []
    def mock_bm25(query, top_k, filters): 
        assert filters == {"court": "Supreme Court"}
        return []
        
    monkeypatch.setattr("backend.services.search_service.search_semantic", mock_semantic)
    monkeypatch.setattr("backend.services.search_service.bm25_service.search", mock_bm25)
    
    response = client.post("/api/search", json={
        "query": "breach",
        "filters": {"court": "Supreme Court"}
    })
    assert response.status_code == 200
