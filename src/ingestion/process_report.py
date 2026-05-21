import argparse
import re
from pathlib import Path

from src.ingestion.pdf_loader import load_pdf_pages, save_pages_to_json
from src.rag.chunking import create_chunks_from_pages, save_chunks_to_json
from src.rag.embeddings import create_chunk_embeddings, save_embeddings


def make_slug(text: str) -> str:
    """
    Convert a company name into a clean file name.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text


def process_report(company: str, year: int, pdf_path: str) -> dict:
    """
    Process one ESG report from PDF to embedded chunks.
    """
    company_slug = make_slug(company)

    pages_path = f"data/processed_text/{company_slug}_{year}_pages.json"
    chunks_path = f"data/processed_text/{company_slug}_{year}_chunks.json"
    embeddings_path = f"data/processed_text/{company_slug}_{year}_chunk_embeddings.json"

    print(f"Processing report for {company} {year}")
    print(f"PDF: {pdf_path}")

    pages = load_pdf_pages(
        pdf_path=pdf_path,
        company=company,
        year=year,
    )

    save_pages_to_json(
        pages=pages,
        output_path=pages_path,
    )

    print(f"Extracted pages: {len(pages)}")
    print(f"Saved pages to: {pages_path}")

    chunks = create_chunks_from_pages(
        pages=pages,
        chunk_size=350,
        overlap=70,
    )

    save_chunks_to_json(
        chunks=chunks,
        output_path=chunks_path,
    )

    print(f"Created chunks: {len(chunks)}")
    print(f"Saved chunks to: {chunks_path}")

    chunks_with_embeddings = create_chunk_embeddings(
        chunks=chunks,
        batch_size=8,
    )

    save_embeddings(
        chunks_with_embeddings=chunks_with_embeddings,
        output_path=embeddings_path,
    )

    print(f"Saved embeddings to: {embeddings_path}")

    print("\nAdd this line to data/evaluation/company_reports.csv if it is a new report:")
    print(f"{company},{year},{embeddings_path}")

    return {
        "company": company,
        "year": year,
        "pdf_path": pdf_path,
        "pages_path": pages_path,
        "chunks_path": chunks_path,
        "embeddings_path": embeddings_path,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--company", required=True)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--pdf", required=True)

    args = parser.parse_args()

    result = process_report(
        company=args.company,
        year=args.year,
        pdf_path=args.pdf,
    )

    print("\nReport processing completed.")
    print(result)