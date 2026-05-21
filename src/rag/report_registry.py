import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS_PATH = ROOT / "data" / "evaluation" / "company_reports.csv"


def load_report_registry(path: Path = REPORTS_PATH) -> list[dict]:
    """
    Load the available company reports from a CSV registry.
    """
    if not path.exists():
        raise FileNotFoundError(f"Report registry not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_embeddings_path(company: str, year: int) -> str:
    """
    Return the embeddings path for a given company and year.
    """
    reports = load_report_registry()

    company_clean = company.strip().lower()
    year_clean = str(year)

    for report in reports:
        same_company = report["company"].strip().lower() == company_clean
        same_year = report["year"].strip() == year_clean

        if same_company and same_year:
            return report["embeddings_path"]

    available = [
        f"{report['company']} {report['year']}"
        for report in reports
    ]

    raise ValueError(
        f"No embeddings path found for {company} {year}. "
        f"Available reports: {available}"
    )