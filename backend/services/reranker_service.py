import json
import google.generativeai as genai
from backend.config import settings

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def rerank_results(query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
    """
    Reranks a list of retrieved documents based on their semantic relevance to the query 
    using Gemini to provide a 'Research Relevance Score' and an explanation.
    """
    if not documents:
        return []
        
    if not settings.GEMINI_API_KEY:
        # Fallback if no API key
        for doc in documents:
            doc["relevance_score"] = doc.get("score", 0) * 100
            doc["reason"] = "Retrieved by keyword or semantic match."
        return sorted(documents, key=lambda x: x["relevance_score"], reverse=True)[:top_k]
        
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    You are an expert legal search relevance evaluator. 
    A user has searched for: "{query}"
    
    You are provided with a list of retrieved case chunks below.
    For each chunk, determine a "Research Relevance Score" between 0 and 100 (where 100 is a perfect match for the user's intent, legal issue, and facts).
    Do NOT call this a probability of winning. It is strictly a "Research Relevance Score".
    
    Also, provide a short, 1-sentence "reason" explaining why it is relevant based ONLY on the retrieved text.
    Example reason: "High relevance because the document discusses contractual breach, delayed performance and damages."
    
    Respond STRICTLY in valid JSON matching this schema:
    [
        {{
            "id": "chunk_id",
            "relevance_score": 95,
            "reason": "..."
        }}
    ]
    
    Results to evaluate:
    """
    
    for res in documents:
        prompt += f"\n--- ID: {res['id']} ---\nText: {res['text']}\n"
        
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        evaluations = json.loads(response.text)
        
        # Merge back into results
        eval_map = {ev["id"]: ev for ev in evaluations}
        
        for res in documents:
            ev = eval_map.get(res["id"])
            if ev:
                res["relevance_score"] = float(ev.get("relevance_score", res.get("score", 0) * 100))
                res["reason"] = ev.get("reason", "Relevant to query.")
            else:
                res["relevance_score"] = float(res.get("score", 0) * 100)
                res["reason"] = "Retrieved by keyword or semantic match."
                
        # Sort by the new cross-encoder score
        reranked_docs = sorted(documents, key=lambda x: x["relevance_score"], reverse=True)
        return reranked_docs[:top_k]
        
    except Exception as e:
        print(f"Reranking error: {e}")
        # Fallback to original score
        for res in documents:
            res["relevance_score"] = float(res.get("score", 0) * 100)
            res["reason"] = "Retrieved by search engine (reranking failed)."
        return sorted(documents, key=lambda x: x["relevance_score"], reverse=True)[:top_k]
