import json
from pathlib import Path


def load_pages(json_path: str):
    file_path = Path(json_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def search_terms(pages, terms):
    for term in terms:
        print(f"\n=== Search term: {term} ===")
        matches = []

        for page in pages:
            text = page["text"].lower()
            if term.lower() in text:
                matches.append(page["page"])

        if matches:
            print(f"Found on pages: {matches[:20]}")
            print(f"Total matching pages: {len(matches)}")
        else:
            print("No matches found.")


if __name__ == "__main__":
    pages = load_pages("data/processed_text/totalenergies_2024_pages.json")

    print(f"Total pages loaded: {len(pages)}")

    terms = [
        "scope 1",
        "scope 2",
        "greenhouse gas",
        "ghg",
        "emissions",
        "taxonomy",
        "capex",
        "transition plan",
        "esrs",
    ]

    search_terms(pages, terms)