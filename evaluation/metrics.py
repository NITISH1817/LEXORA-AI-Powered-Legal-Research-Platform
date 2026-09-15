import json

def calculate_precision_at_k(retrieved_ids, relevant_ids, k):
    if not retrieved_ids[:k]: return 0.0
    relevant_retrieved = set(retrieved_ids[:k]).intersection(set(relevant_ids))
    return len(relevant_retrieved) / float(k)

def calculate_recall_at_k(retrieved_ids, relevant_ids, k):
    if not relevant_ids: return 1.0
    relevant_retrieved = set(retrieved_ids[:k]).intersection(set(relevant_ids))
    return len(relevant_retrieved) / float(len(relevant_ids))

def calculate_mrr(retrieved_ids, relevant_ids):
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0

def evaluate_faithfulness(answer_text, required_sources, forbidden_claims):
    # Deterministic check for this POC. 
    # In a full production system, use LLM-as-a-judge for semantic similarity.
    score = 1.0
    answer_lower = answer_text.lower()
    
    # Check if abstained correctly
    if "insufficient evidence" in answer_lower:
        if not required_sources: # We expected abstention
            return 1.0
        return 0.0 # We abstained but shouldn't have
        
    for fc in forbidden_claims:
        if fc.lower() in answer_lower:
            score -= 0.5 # Penalty for hallucination
            
    # Check source citations (e.g. "[case_001")
    citation_coverage = 0
    for req in required_sources:
        # Just check if source ID string is loosely mentioned in the text
        if req.split(":")[0] in answer_lower:
            citation_coverage += 1
            
    cov_ratio = citation_coverage / max(len(required_sources), 1)
    
    return max(0.0, score * cov_ratio)
