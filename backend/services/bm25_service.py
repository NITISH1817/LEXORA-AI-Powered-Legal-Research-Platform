import os
import json
import pickle
from rank_bm25 import BM25Okapi

BM25_INDEX_PATH = "./chroma_db/bm25_index.pkl"
BM25_CORPUS_PATH = "./chroma_db/bm25_corpus.json"

class BM25Service:
    def __init__(self):
        self.bm25_model = None
        self.bm25_corpus = [] # List of dicts: {"id": chunk_id, "text": text, "metadata": metadata}
        self.load_bm25()

    def load_bm25(self):
        if os.path.exists(BM25_INDEX_PATH) and os.path.exists(BM25_CORPUS_PATH):
            try:
                with open(BM25_INDEX_PATH, "rb") as f:
                    self.bm25_model = pickle.load(f)
                with open(BM25_CORPUS_PATH, "r") as f:
                    self.bm25_corpus = json.load(f)
            except Exception:
                self.bm25_model = None
                self.bm25_corpus = []

    def save_bm25(self):
        os.makedirs("./chroma_db", exist_ok=True)
        with open(BM25_INDEX_PATH, "wb") as f:
            pickle.dump(self.bm25_model, f)
        with open(BM25_CORPUS_PATH, "w") as f:
            json.dump(self.bm25_corpus, f)

    def build_bm25_from_corpus(self):
        tokenized_corpus = [doc["text"].lower().split() for doc in self.bm25_corpus]
        self.bm25_model = BM25Okapi(tokenized_corpus)
        self.save_bm25()

    def index_chunk(self, chunk_id: str, text: str, metadata: dict):
        self.bm25_corpus.append({"id": chunk_id, "text": text, "metadata": metadata})
        self.build_bm25_from_corpus()

    def search(self, query: str, top_k: int = 10, filters: dict = None):
        if not self.bm25_model or not self.bm25_corpus:
            return []
            
        tokenized_query = query.lower().split()
        scores = self.bm25_model.get_scores(tokenized_query)
        
        doc_scores = list(zip(self.bm25_corpus, scores))
        
        if filters:
            filtered_doc_scores = []
            for doc, score in doc_scores:
                meta = doc["metadata"]
                match = True
                for k, v in filters.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if match:
                    filtered_doc_scores.append((doc, score))
            doc_scores = filtered_doc_scores
            
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        parsed_results = []
        for doc, score in doc_scores[:top_k]:
            if score > 0:
                parsed_results.append({
                    "id": doc["id"],
                    "score": score,
                    "metadata": doc["metadata"],
                    "text": doc["text"],
                    "source": "keyword"
                })
                
        return parsed_results

    def remove_chunk(self, chunk_id: str):
        """
        Remove a chunk from the BM25 corpus by ID.
        Used during document deletion and idempotent retry.
        Rebuilds the index after removal.
        """
        original_len = len(self.bm25_corpus)
        self.bm25_corpus = [doc for doc in self.bm25_corpus if doc["id"] != chunk_id]
        if len(self.bm25_corpus) < original_len:
            if self.bm25_corpus:
                self.build_bm25_from_corpus()
            else:
                self.bm25_model = None
                self.save_bm25()

bm25_service = BM25Service()
