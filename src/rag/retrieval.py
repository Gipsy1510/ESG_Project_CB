"""
Retrieval from ChromaDB vector store.
"""

from typing import List, Dict
from src.rag.embeddings import get_albert_config, embed_texts_with_requests
from src.rag.vector_store import query_index


def embed_query(query: str) -> List[float]:
    config = get_albert_config()
    return embed_texts_with_requests([query], config)[0]


def keyword_boost(query: str, chunk: Dict) -> float:
    query_lower = query.lower()
    text_lower  = chunk.get("text", "").lower()
    boost       = 0.0

    taxonomy_query = any(
        term in query_lower
        for term in ["taxonomy", "capex", "aligned", "eligible"]
    )

    if taxonomy_query:
        weighted_terms = {
            "taxonomy":            0.04,
            "capex":               0.05,
            "aligned":             0.06,
            "eligible":            0.03,
            "aligned activities":  0.08,
            "eligible activities": 0.06,
            "turnover capex":      0.10,
            "controlled perimeter":0.08,
            "controlled scope":    0.04,
            "proportional view":   0.03,
            "total %":             0.12,
            "total":               0.04,
            "2022 2023":           0.06,
        }
        for term, value in weighted_terms.items():
            if term in text_lower:
                boost += value

        if "total" in query_lower and "total %" in text_lower:
            boost += 0.08
        if "controlled" in query_lower and (
            "controlled perimeter" in text_lower or "controlled scope" in text_lower
        ):
            boost += 0.08
        if "aligned capex" in query_lower and (
            "aligned activities" in text_lower and "capex" in text_lower
        ):
            boost += 0.08

    return boost


def retrieve_top_chunks(
    query:   str,
    top_k:   int = 5,
    company: str | None = None,
    year:    str | None = None,
) -> List[Dict]:
    """
    Embed query, search ChromaDB, apply keyword boost, return top-k chunks.
    Fetches top_k * 3 candidates first so boosting can re-rank meaningfully.
    """
    query_embedding = embed_query(query)

    candidates = query_index(
        query_embedding = query_embedding,
        top_k           = top_k * 3,
        company         = company,
        year            = year,
    )

    for chunk in candidates:
        boost                  = keyword_boost(query, chunk)
        chunk["keyword_boost"] = boost
        chunk["score"]         = round(chunk["score"] + boost, 4)

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:top_k]