"""
Batch process all ESG reports from report_inventory.csv.
Runs each PDF through: pdf_loader -> chunking -> embeddings -> saves JSON.

Usage:
    python src/ingestion/process_all_reports.py
    python src/ingestion/process_all_reports.py --skip-existing   # skip already processed
    python src/ingestion/process_all_reports.py --company totalenergies  # one company only
"""

import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_CSV = ROOT / "data" / "metadata" / "report_inventory.csv"

# import after ROOT is set so relative imports work
import sys
sys.path.insert(0, str(ROOT))

from src.ingestion.process_report import process_report


def make_slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def load_inventory() -> list[dict]:
    if not INVENTORY_CSV.exists():
        raise FileNotFoundError(f"Inventory not found: {INVENTORY_CSV}")
    with INVENTORY_CSV.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def already_processed(company_slug: str, year: str) -> bool:
    embeddings_path = ROOT / "data" / "processed_text" / f"{company_slug}_{year}_chunk_embeddings.json"
    return embeddings_path.exists()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip reports that already have embeddings")
    parser.add_argument("--company", type=str, default=None,
                        help="Only process reports for this company slug (e.g. totalenergies)")
    args = parser.parse_args()

    reports = load_inventory()
    print(f"Found {len(reports)} reports in inventory\n")

    succeeded, failed, skipped = [], [], []

    for row in reports:
        company     = row["company"]          # folder name slug e.g. "totalenergies"
        year        = row["year"]
        pdf_path    = row["local_path"]
        company_slug = make_slug(company)

        # optional company filter
        if args.company and company_slug != make_slug(args.company):
            continue

        # optional skip
        if args.skip_existing and already_processed(company_slug, year):
            print(f"  SKIP  {company} {year}  (already processed)")
            skipped.append((company, year))
            continue

        if not Path(pdf_path).exists():
            print(f"  MISSING PDF  {company} {year}  →  {pdf_path}")
            failed.append((company, year, "PDF not found"))
            continue

        print(f"  Processing  {company} {year}  ...")

        try:
            process_report(
                company=company,
                year=int(year),
                pdf_path=pdf_path,
            )
            succeeded.append((company, year))
            print(f"  OK  {company} {year}\n")

        except Exception as e:
            print(f"  FAILED  {company} {year}  →  {e}\n")
            failed.append((company, year, str(e)))

    print("\n" + "=" * 60)
    print(f"Done.  Succeeded: {len(succeeded)}  |  Skipped: {len(skipped)}  |  Failed: {len(failed)}")

    if failed:
        print("\nFailed reports:")
        for item in failed:
            print(f"  {item[0]} {item[1]}  →  {item[2]}")


if __name__ == "__main__":
    main()