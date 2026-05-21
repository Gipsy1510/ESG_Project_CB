"""
Builds and queries a ChromaDB vector store from all processed ESG report embeddings.

Usage:
    # Build the index from all embedding JSONs
    python src/rag/vector_store.py --build

    # Test a query against the index
    python src/rag/vector_store.py --query "What are Shell Scope 1 emissions?"
"""

import argparse
import json
from pathlib import Path

import chromadb
from tqdm import tqdm

ROOT         = Path(__file__).resolve().parents[2]
PROCESSED    = ROOT / "data" / "processed_text"
CHROMA_DIR   = ROOT / "data" / "vector_store"
COLLECTION   = "esg_reports"


def get_collection(read_only: bool = False) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def build_index() -> None:
    embedding_files = sorted(PROCESSED.glob("*_chunk_embeddings.json"))

    if not embedding_files:
        raise FileNotFoundError(f"No embedding files found in {PROCESSED}")

    print(f"Found {len(embedding_files)} embedding files\n")

    collection = get_collection()
    existing   = set(collection.get()["ids"])
    print(f"Existing chunks in index: {len(existing)}")

    for emb_file in tqdm(embedding_files, desc="Indexing files"):
        with emb_file.open("r", encoding="utf-8") as f:
            chunks = json.load(f)

        # filter out chunks already in the index and those without embeddings
        new_chunks = [
            c for c in chunks
            if c.get("embedding") and c["chunk_id"] not in existing
        ]

        if not new_chunks:
            continue

        batch_size = 100
        for start in range(0, len(new_chunks), batch_size):
            batch = new_chunks[start : start + batch_size]

            collection.add(
                ids        = [c["chunk_id"] for c in batch],
                embeddings = [c["embedding"] for c in batch],
                documents  = [c["text"] for c in batch],
                metadatas  = [
                    {
                        "company":     c["company"],
                        "year":        str(c["year"]),
                        "page":        int(c["page"]),
                        "source_file": c.get("source_file", ""),
                    }
                    for c in batch
                ],
            )

        existing.update(c["chunk_id"] for c in new_chunks)

    total = collection.count()
    print(f"\nIndex built. Total chunks in vector store: {total}")


def query_index(
    query_embedding: list[float],
    top_k: int = 5,
    company: str | None = None,
    year: str | None = None,
) -> list[dict]:
    """
    Query the vector store and return top-k chunks with metadata.
    Optionally filter by company and/or year.
    """
    collection = get_collection()

    where = {}
    company_clean = company.lower().strip() if company else None
    year_clean    = str(year).strip() if year else None

    if company_clean and year_clean:
        where = {"$and": [{"company": company_clean}, {"year": year_clean}]}
    elif company_clean:
        where = {"company": company_clean}
    elif year_clean:
        where = {"year": year_clean}

    kwargs = dict(
        query_embeddings = [query_embedding],
        n_results        = top_k,
        include          = ["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "chunk_id":   meta.get("chunk_id", ""),
            "company":    meta["company"],
            "year":       meta["year"],
            "page":       meta["page"],
            "text":       doc,
            "score":      round(1 - dist, 4),  # cosine distance → similarity
        })

    return chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="Build the ChromaDB index")
    parser.add_argument("--query", type=str, help="Test query string")
    parser.add_argument("--company", type=str, default=None)
    parser.add_argument("--year", type=str, default=None)
    args = parser.parse_args()

    if args.build:
        build_index()

    if args.query:
        import sys
        sys.path.insert(0, str(ROOT))
        from src.rag.embeddings import get_albert_config, embed_texts_with_requests

        config    = get_albert_config()
        embedding = embed_texts_with_requests([args.query], config)[0]

        results = query_index(
            query_embedding = embedding,
            top_k           = 5,
            company         = args.company,
            year            = args.year,
        )

        print(f"\nTop results for: '{args.query}'\n")
        for i, r in enumerate(results, 1):
            print(f"[{i}] {r['company']} {r['year']} p{r['page']}  score={r['score']}")
            print(f"     {r['text'][:200]}\n")