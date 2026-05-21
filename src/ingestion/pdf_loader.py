from pathlib import Path
from typing import Dict, List
import json

import pdfplumber


def load_pdf_pages(pdf_path: str, company: str, year: int) -> List[Dict]:
    """
    Extract text from a PDF page by page.

    The output keeps metadata that will be needed later for citations,
    retrieval filtering, and ESG evidence tracking.
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_file}")

    pages = []

    with pdfplumber.open(pdf_file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            pages.append(
                {
                    "company": company,
                    "year": year,
                    "page": page_number,
                    "source_file": pdf_file.name,
                    "text": text.strip(),
                }
            )

    return pages


def save_pages_to_json(pages: List[Dict], output_path: str) -> None:
    """
    Save extracted pages to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    pdf_path = "data/raw_reports/sample_report.pdf"
    company = "TotalEnergies"
    year = 2024

    pages = load_pdf_pages(pdf_path=pdf_path, company=company, year=year)

    output_path = "data/processed_text/totalenergies_2024_pages.json"
    save_pages_to_json(pages, output_path)

    print(f"Extracted {len(pages)} pages.")
    print(f"Saved output to: {output_path}")

    if pages:
        print("\nPreview of page 1:")
        print(pages[0]["text"][:800])