"""
Information Retrieval Evaluation Metrics (Recall@K, nDCG@K, MRR).
"""

import math
from typing import Dict, List, Set
from pydantic import BaseModel, Field


class RetrievalMetrics(BaseModel):
    """Evaluation summary for a single query or averaged across benchmark query set."""
    recall_at_10: float = Field(..., ge=0.0, le=1.0)
    ndcg_at_10: float = Field(..., ge=0.0, le=1.0)
    mrr: float = Field(..., ge=0.0, le=1.0)
    latency_ms: float = Field(..., ge=0.0)


def compute_recall_at_k(retrieved_page_ids: List[str], relevant_page_ids: Set[str], k: int = 10) -> float:
    """Computes Recall@K."""
    if not relevant_page_ids:
        return 0.0
    top_k = set(retrieved_page_ids[:k])
    hits = len(top_k & relevant_page_ids)
    return hits / len(relevant_page_ids)


def compute_mrr(retrieved_page_ids: List[str], relevant_page_ids: Set[str]) -> float:
    """Computes Mean Reciprocal Rank (first relevant item rank)."""
    for rank, pid in enumerate(retrieved_page_ids, start=1):
        if pid in relevant_page_ids:
            return 1.0 / rank
    return 0.0


def compute_ndcg_at_k(retrieved_page_ids: List[str], relevance_scores: Dict[str, float], k: int = 10) -> float:
    """
    Computes Normalized Discounted Cumulative Gain (nDCG@K).
    Relevance scores are graded (e.g. 0 to 3).
    """
    top_k = retrieved_page_ids[:k]
    dcg = 0.0
    for i, pid in enumerate(top_k, start=1):
        rel = relevance_scores.get(pid, 0.0)
        dcg += (2.0**rel - 1.0) / math.log2(i + 1)

    # Ideal DCG
    ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_scores, start=1):
        idcg += (2.0**rel - 1.0) / math.log2(i + 1)

    if idcg <= 0.0:
        return 0.0
    return min(1.0, dcg / idcg)
