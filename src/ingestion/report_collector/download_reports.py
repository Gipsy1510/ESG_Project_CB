"""
ESG report downloader.
Pass 1: requests. Pass 2: Playwright for anything blocked or returning HTML.

    pip install requests tqdm playwright
    playwright install chromium
"""

from pathlib import Path
import hashlib, re, time, tempfile
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse
from tqdm import tqdm
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT      = Path(__file__).resolve().parents[3]
INPUT_CSV = ROOT / "data" / "metadata" / "report_links.csv"
OUT_DIR   = ROOT / "data" / "raw_reports"
INVENTORY = ROOT / "data" / "metadata" / "report_inventory.csv"
FAILED    = ROOT / "data" / "metadata" / "failed_downloads.csv"
YEARS     = ["2025", "2024", "2023", "2022", "2021", "2020"]


def slugify(t):
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def is_pdf(b):
    return b.startswith(b"%PDF") and len(b) > 10_000

def save(content, company, year):
    d = sha256(content)
    p = OUT_DIR / slugify(company) / year
    p.mkdir(parents=True, exist_ok=True)
    f = p / f"{slugify(company)}_{year}_{d[:8]}.pdf"
    f.write_bytes(content)
    return f, d

def record(company, year, url, path, content):
    return {"company": company, "reporting_year": int(year), "pdf_url": url,
            "local_path": str(path), "file_hash": sha256(content),
            "size_mb": round(len(content) / 1e6, 2), "download_status": "success"}

def failure(company, year, url, error):
    return {"company": company, "reporting_year": year,
            "pdf_url": url, "error": error, "download_status": "failed"}

def load(path):
    if not path.exists():
        return [], set()
    df = pd.read_csv(path, dtype=str)
    return df.to_dict("records"), set(df["pdf_url"].dropna())

def headers(url):
    origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9", "Referer": origin}

def make_session():
    s = requests.Session()
    r = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=r))
    s.mount("http://",  HTTPAdapter(max_retries=r))
    return s

def try_requests(session, url):
    """Returns (content|None, error|None, fallback:bool)."""
    try:
        chunks = []
        with session.get(url, headers=headers(url), timeout=60,
                         allow_redirects=True, stream=True) as r:
            if r.status_code in {401, 403, 406}:
                return None, f"{r.status_code} blocked", True
            r.raise_for_status()
            ct = r.headers.get("Content-Type", "")
            for chunk in r.iter_content(8192):
                if chunk:
                    chunks.append(chunk)
        content = b"".join(chunks)
        if not is_pdf(content):
            return None, f"Not a PDF (Content-Type: {ct})", "html" in ct.lower()
        return content, None, False
    except Exception as e:
        return None, str(e), False

def try_playwright(context, url):
    """Returns PDF bytes or None.

    Chromium always triggers a file download for direct PDF URLs — page.goto
    raises 'Download is starting' if the context doesn't accept downloads.
    We use a fresh page with accept_downloads=True for every URL.
    """
    page = context.new_page()
    try:
        with page.expect_download(timeout=60_000) as dl_info:
            try:
                page.goto(url, timeout=60_000)
            except Exception:
                pass  # 'Download is starting' is expected and fine
        download = dl_info.value
        content = Path(download.path()).read_bytes()
        return content if is_pdf(content) else None
    except PWTimeout:
        return None
    except Exception:
        # URL is an HTML viewer — try grabbing PDF from response or frame
        try:
            resp = page.goto(url, wait_until="networkidle", timeout=60_000)
            if resp and is_pdf(body := resp.body()):
                return body
            for frame in page.frames:
                if ".pdf" in frame.url.lower():
                    try:
                        b = page.request.get(frame.url).body()
                        if is_pdf(b):
                            return b
                    except Exception:
                        pass
        except Exception:
            pass
        return None
    finally:
        page.close()


def main():
    try:
        df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(INPUT_CSV, encoding="latin-1")

    done, seen_success = load(INVENTORY)
    _, seen_failed     = load(FAILED)
    skip = seen_success - seen_failed   # only skip confirmed successes

    session   = make_session()
    successes, failures, pw_queue = [], [], []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="requests"):
        company = row["Companies"]
        for year in YEARS:
            raw = row.get(year)
            if pd.isna(raw) or not str(raw).strip():
                continue
            url = str(raw).strip().split("#")[0]
            if url in skip:
                continue
            content, err, fallback = try_requests(session, url)
            if content:
                p, _ = save(content, company, year)
                successes.append(record(company, year, url, p, content))
                skip.add(url)
            elif fallback:
                pw_queue.append((company, year, url))
            else:
                failures.append(failure(company, year, url, err))
            time.sleep(1.5)

    if pw_queue:
        print(f"\nPlaywright: {len(pw_queue)} blocked URLs")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                accept_downloads=True,
            )
            for company, year, url in tqdm(pw_queue, desc="playwright"):
                content = try_playwright(ctx, url)
                if content:
                    p_, _ = save(content, company, year)
                    successes.append(record(company, year, url, p_, content))
                else:
                    failures.append(failure(company, year, url, "Playwright: no PDF returned"))
                time.sleep(2.0)
            browser.close()

    recovered = {r["pdf_url"] for r in successes}
    all_inv  = pd.DataFrame([r for r in done if r["download_status"] == "success"] + successes)
    all_fail = pd.DataFrame([r for r in (load(FAILED)[0]) if r["pdf_url"] not in recovered] + failures)

    if not all_inv.empty:
        all_inv.drop_duplicates("pdf_url", keep="last").to_csv(INVENTORY, index=False)
    if not all_fail.empty:
        all_fail.drop_duplicates("pdf_url", keep="last").to_csv(FAILED, index=False)
    elif FAILED.exists():
        FAILED.unlink()

    print(f"New: {len(successes)}  |  Failed: {len(failures)}  |  Total: {len(all_inv)}")


if __name__ == "__main__":
    main()