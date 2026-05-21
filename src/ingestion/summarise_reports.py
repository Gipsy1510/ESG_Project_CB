# run once from your project root
from pathlib import Path
import csv

ROOT = Path("data/raw_reports")
rows = []

for company_folder in sorted(ROOT.iterdir()):
    if not company_folder.is_dir():
        continue
    for year_folder in sorted(company_folder.iterdir()):
        if not year_folder.is_dir():
            continue
        for pdf in year_folder.glob("*.pdf"):
            rows.append({
                "company": company_folder.name,
                "year": year_folder.name,
                "local_path": str(pdf),
            })

with open("data/metadata/report_inventory.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["company", "year", "local_path"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Found {len(rows)} reports")