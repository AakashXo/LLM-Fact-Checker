"""
PIB Scraper

Usage:
    # From project root (llm_fact_checker/)
    python -m src.pib_scraper --limit 50

This will:
- Fetch latest PIB press releases from RSS
- Visit each press release page
- Extract main text
- Save them as rows in data/facts.csv
"""

import argparse
import csv
import email.utils
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from src.config import DATA_DIR, FACTS_CSV_PATH

# Default PIB RSS feed for English press releases
PIB_RSS_URL = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"


@dataclass
class PibItem:
    title: str
    link: str
    pub_date: Optional[str]


def fetch_rss_items(limit: int = 50) -> List[PibItem]:
    """Fetch and parse PIB RSS feed, return a list of PibItem."""
    print(f"[RSS] Fetching RSS feed from {PIB_RSS_URL}")
    resp = requests.get(PIB_RSS_URL, timeout=20)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    items = []
    for item in root.findall("./channel/item"):
        title_el = item.find("title")
        link_el = item.find("link")
        date_el = item.find("pubDate")

        if title_el is None or link_el is None:
            continue

        title = title_el.text.strip() if title_el.text else ""
        link = link_el.text.strip() if link_el.text else ""
        pub_date_raw = date_el.text.strip() if date_el is not None and date_el.text else None

        items.append(PibItem(title=title, link=link, pub_date=pub_date_raw))

        if len(items) >= limit:
            break

    print(f"[RSS] Got {len(items)} items from RSS")
    return items


def parse_pub_date(pub_date_raw: Optional[str]) -> str:
    """
    Convert RSS pubDate string to YYYY-MM-DD.
    If parsing fails or missing, use today's date.
    """
    if not pub_date_raw:
        return datetime.utcnow().date().isoformat()

    try:
        dt = email.utils.parsedate_to_datetime(pub_date_raw)
        return dt.date().isoformat()
    except Exception:
        return datetime.utcnow().date().isoformat()


def extract_main_text_from_press_release(url: str) -> str:
    """
    Fetch the PIB press release page and extract main text.

    Heuristic:
    - Prefer text inside <p> tags
    - If no <p> tags, fall back to body text
    - Join first few paragraphs into a single statement
    """
    print(f"[PAGE] Fetching press release: {url}")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")

    # Try to get all paragraphs
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]

    if not paragraphs:
        # Fallback: take the main body text
        body = soup.find("body")
        if body:
            text = body.get_text(" ", strip=True)
        else:
            text = soup.get_text(" ", strip=True)
        # Limit length so it’s not huge
        return text[:1000]

    # Take first 3–4 non-empty paragraphs as main fact text
    non_empty = [p for p in paragraphs if p]
    main_paras = non_empty[:4]
    statement = " ".join(main_paras)

    # Optional: truncate very long text
    if len(statement) > 1500:
        statement = statement[:1500] + "..."
    return statement


def build_facts_from_pib(limit: int = 50) -> List[dict]:
    """
    Fetch PIB RSS, visit each press release, and build fact rows.
    Each fact row is a dict matching the CSV columns.
    """
    items = fetch_rss_items(limit=limit)
    facts = []

    for idx, item in enumerate(items, start=1):
        date_iso = parse_pub_date(item.pub_date)
        try:
            statement = extract_main_text_from_press_release(item.link)
        except Exception as e:
            print(f"[WARN] Failed to scrape {item.link}: {e}", file=sys.stderr)
            continue

        fact = {
            "id": idx,
            "source": "PIB",
            "date": date_iso,
            "statement": statement,
            "title": item.title,
            "url": item.link,
        }
        facts.append(fact)

    print(f"[FACTS] Built {len(facts)} fact rows from PIB")
    return facts


def write_facts_to_csv(facts: List[dict], path: Path):
    """
    Write facts to CSV at the given path.

    Columns:
    - id, source, date, statement, title, url
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["id", "source", "date", "statement", "title", "url"]
    print(f"[CSV] Writing {len(facts)} rows to {path}")

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in facts:
            writer.writerow(row)

    print("[CSV] Done.")


def main():
    parser = argparse.ArgumentParser(description="Scrape PIB press releases into facts.csv")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of latest PIB items to fetch from RSS (default: 50)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(FACTS_CSV_PATH),
        help=f"Path to output CSV (default: {FACTS_CSV_PATH})",
    )

    args = parser.parse_args()

    output_path = Path(args.output)

    facts = build_facts_from_pib(limit=args.limit)
    if not facts:
        print("[ERROR] No facts extracted. Aborting.")
        sys.exit(1)

    write_facts_to_csv(facts, output_path)
    print("[OK] PIB facts CSV ready.")


if __name__ == "__main__":
    main()
