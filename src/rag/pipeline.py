"""
Full RAG pipeline: retrieve from ChromaDB → generate answer via Albert.
Called by the Streamlit app.
"""

from typing import Dict
from src.rag.retrieval import retrieve_top_chunks
from src.rag.answer_generation import generate_answer


def run_rag_question(
    question: str,
    company:  str | None = None,
    year:     int | None = None,
    top_k:    int = 5,
) -> Dict:
    """
    Run the full RAG pipeline for one question.
    company and year are optional filters — if omitted, searches all reports.
    """
    retrieved_chunks = retrieve_top_chunks(
        query   = question,
        top_k   = top_k,
        company = company.lower().strip() if company else None,
        year    = str(year) if year else None,
    )

    answer = generate_answer(
        question         = question,
        retrieved_chunks = retrieved_chunks,
    )

    sources = [
        {
            "source_number": idx,
            "company":       chunk["company"],
            "year":          chunk["year"],
            "page":          chunk["page"],
            "score":         chunk["score"],
            "text_preview":  chunk["text"][:500],
        }
        for idx, chunk in enumerate(retrieved_chunks, 1)
    ]

    return {
        "question": question,
        "company":  company,
        "year":     year,
        "answer":   answer,
        "sources":  sources,
    }


if __name__ == "__main__":
    result = run_rag_question(
        question = "What are Shell Scope 1 and Scope 2 GHG emissions?",
        company  = "shell",
        year     = 2024,
    )

    print("\nQUESTION:", result["question"])
    print("\nANSWER:")
    print(result["answer"])
    print("\nSOURCES:")
    for s in result["sources"]:
        print(f"  [{s['source_number']}] {s['company']} {s['year']} p{s['page']}  score={s['score']}")