import json
import os
from pathlib import Path
from typing import Dict, List

import requests
from dotenv import load_dotenv
from tqdm import tqdm


def load_chunks(input_path: str) -> List[Dict]:
    """
    Load chunks generated from the PDF text.
    """
    file_path = Path(input_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_embeddings(chunks_with_embeddings: List[Dict], output_path: str) -> None:
    """
    Save chunks with their embeddings to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(chunks_with_embeddings, f, ensure_ascii=False)


def get_albert_config() -> Dict[str, str]:
    """
    Read Albert API configuration from the local .env file.
    """
    load_dotenv()

    api_key = os.getenv("ALBERT_API_KEY")
    base_url = os.getenv("ALBERT_BASE_URL")
    model = os.getenv("ALBERT_EMBEDDING_MODEL", "BAAI/bge-m3")

    if not api_key:
        raise ValueError("ALBERT_API_KEY is missing. Check your .env file.")

    if not base_url:
        raise ValueError("ALBERT_BASE_URL is missing. Check your .env file.")

    return {
        "api_key": api_key,
        "base_url": base_url.rstrip("/"),
        "model": model,
    }


def embed_texts_with_requests(texts: List[str], config: Dict[str, str]) -> List[List[float]]:
    """
    Create embeddings using Albert API directly with requests.

    We use requests instead of the OpenAI Python client because the direct
    endpoint worked reliably during testing.
    """
    url = f"{config['base_url']}/embeddings"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config["model"],
        "input": texts,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"Embedding request failed with status {response.status_code}: "
            f"{response.text[:1000]}"
        )

    data = response.json()
    return [item["embedding"] for item in data["data"]]


def create_chunk_embeddings(
    chunks: List[Dict],
    batch_size: int = 8,
) -> List[Dict]:
    """
    Add embeddings to each chunk.

    Empty or extremely short chunks are skipped because they add noise and can
    make retrieval less useful.
    """
    config = get_albert_config()

    valid_chunks = [
        chunk for chunk in chunks
        if chunk.get("text") and len(chunk["text"].strip()) > 20
    ]

    print(f"Total chunks: {len(chunks)}")
    print(f"Valid chunks for embedding: {len(valid_chunks)}")
    print(f"Embedding model: {config['model']}")

    chunks_with_embeddings = []

    for start in tqdm(range(0, len(valid_chunks), batch_size), desc="Embedding chunks"):
        batch = valid_chunks[start:start + batch_size]

        texts = [
            chunk["text"][:8000]
            for chunk in batch
        ]

        try:
            embeddings = embed_texts_with_requests(
                texts=texts,
                config=config,
            )

            for chunk, embedding in zip(batch, embeddings):
                chunk_copy = dict(chunk)
                chunk_copy["embedding"] = embedding
                chunks_with_embeddings.append(chunk_copy)

        except Exception as error:
            print("\nEmbedding failed.")
            print(f"Batch start index: {start}")
            print(f"Chunk IDs: {[chunk['chunk_id'] for chunk in batch]}")
            raise error

    return chunks_with_embeddings


if __name__ == "__main__":
    input_path = "data/processed_text/totalenergies_2024_chunks.json"
    output_path = "data/processed_text/totalenergies_2024_chunk_embeddings.json"

    chunks = load_chunks(input_path)

    chunks_with_embeddings = create_chunk_embeddings(
        chunks=chunks,
        batch_size=8,
    )

    save_embeddings(chunks_with_embeddings, output_path)

    print(f"\nSaved embeddings to: {output_path}")

    if chunks_with_embeddings:
        first = chunks_with_embeddings[0]
        print("\nPreview:")
        print(f"Chunk ID: {first['chunk_id']}")
        print(f"Embedding length: {len(first['embedding'])}")
        print(f"Text preview: {first['text'][:200]}")