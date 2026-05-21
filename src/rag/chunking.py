from pathlib import Path
from typing import Dict, List
import json
import re


def load_json(json_path: str) -> List[Dict]:
    """
    Load a JSON file containing extracted PDF pages.
    """
    file_path = Path(json_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def clean_text(text: str) -> str:
    """
    Apply light text cleaning.

    We keep this simple on purpose: the goal is not to over-clean the report,
    but to remove excessive spaces and line breaks that can hurt retrieval.
    """
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text_into_chunks(
    text: str,
    chunk_size: int = 350,
    overlap: int = 70,
) -> List[str]:
    """
    Split text into overlapping word-based chunks.

    This is an approximation of token-based chunking. It is simple, transparent,
    and good enough for the first MVP.
    """
    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def create_chunks_from_pages(
    pages: List[Dict],
    chunk_size: int = 350,
    overlap: int = 70,
) -> List[Dict]:
    """
    Create chunks from extracted PDF pages while preserving page-level metadata.
    """
    all_chunks = []

    for page in pages:
        cleaned_text = clean_text(page.get("text", ""))

        if not cleaned_text:
            continue

        page_chunks = split_text_into_chunks(
            text=cleaned_text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for idx, chunk_text in enumerate(page_chunks, start=1):
            chunk_id = (
                f"{page['company'].lower().replace(' ', '_')}_"
                f"{page['year']}_p{page['page']:03d}_c{idx:02d}"
            )

            all_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "company": page["company"],
                    "year": page["year"],
                    "page": page["page"],
                    "source_file": page["source_file"],
                    "text": chunk_text,
                }
            )

    return all_chunks


def save_chunks_to_json(chunks: List[Dict], output_path: str) -> None:
    """
    Save chunks to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    input_path = "data/processed_text/totalenergies_2024_pages.json"
    output_path = "data/processed_text/totalenergies_2024_chunks.json"

    pages = load_json(input_path)

    chunks = create_chunks_from_pages(
        pages=pages,
        chunk_size=350,
        overlap=70,
    )

    save_chunks_to_json(chunks, output_path)

    print(f"Loaded pages: {len(pages)}")
    print(f"Created chunks: {len(chunks)}")
    print(f"Saved output to: {output_path}")

    if chunks:
        print("\nPreview of first chunk:")
        print(f"Chunk ID: {chunks[0]['chunk_id']}")
        print(f"Page: {chunks[0]['page']}")
        print(chunks[0]["text"][:800])