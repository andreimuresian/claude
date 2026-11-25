#!/usr/bin/env python3
"""
Download the UCIMU catalog page of each Lombardy member and extract what it makes.

Usage:
    pip install requests beautifulsoup4
    python ucimu_scrape.py

Output (folder ./out):
    html/<slug>.html     raw page, kept so the parsing can be redone offline
    companies.csv        one row per company: status, title, technology categories, website, text excerpt
    failed.txt           slugs that could not be downloaded

Then zip the ./out folder and send it back.

It is polite on purpose: one request every ~2 seconds (142 pages = about 5 minutes),
it checks robots.txt first and stops if the catalog pages are disallowed.
"""
import csv
import json
import re
import sys
import time
from pathlib import Path
from urllib import robotparser

import requests
from bs4 import BeautifulSoup

BASE = "https://www.ucimu.it"
HERE = Path(__file__).resolve().parent
OUT = Path("out")
HTML_DIR = OUT / "html"
DELAY_SECONDS = 2.0
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; personal-research-script)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

members = json.loads((HERE / "lombardy_members.json").read_text(encoding="utf-8"))
taxonomy = json.loads((HERE / "taxonomy.json").read_text(encoding="utf-8"))


def allowed_by_robots(session):
    rp = robotparser.RobotFileParser()
    try:
        resp = session.get(f"{BASE}/robots.txt", headers=HEADERS, timeout=20)
        if resp.status_code >= 400:
            return True  # no robots.txt = nothing disallowed
        rp.parse(resp.text.splitlines())
    except requests.RequestException:
        return True
    return rp.can_fetch(HEADERS["User-Agent"], f"{BASE}/catalogo/imprese/v/test/")


def fetch(session, slug):
    url = f"{BASE}/catalogo/imprese/v/{slug}/"
    last_status = None
    for attempt in range(3):
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            last_status = resp.status_code
            if resp.status_code == 200:
                return resp.text, 200
            if resp.status_code in (403, 404, 410):
                return None, resp.status_code
        except requests.RequestException as exc:
            last_status = str(exc)[:60]
        time.sleep(3 * (attempt + 1))
    return None, last_status


def parse(html, slug):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else (soup.title.get_text(strip=True) if soup.title else "")

    # technology categories linked from the page, e.g. .../repertorio-tecnologico/v/3-1-0/
    cats = []
    for a in soup.find_all("a", href=True):
        m = re.search(r"repertorio-tecnologico/v/([\d-]+)/?", a["href"])
        if m:
            code = m.group(1).replace("-", ".")
            label = taxonomy.get(code) or a.get_text(" ", strip=True) or code
            if label not in cats:
                cats.append(label)

    # external website of the company, if any
    site = ""
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and "ucimu.it" not in href and not any(
            s in href for s in ("facebook.", "linkedin.", "twitter.", "instagram.", "youtube.", "google.", "maps.")
        ):
            site = href
            break

    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    return {
        "title": title,
        "categories": " | ".join(cats),
        "website": site,
        "text_excerpt": text[:1500],
    }


def main():
    OUT.mkdir(exist_ok=True)
    HTML_DIR.mkdir(exist_ok=True)
    session = requests.Session()

    if not allowed_by_robots(session):
        print("robots.txt disallows these pages - stopping. Nothing was downloaded.")
        sys.exit(1)

    rows, failed = [], []
    for i, m in enumerate(members, 1):
        slug = m["slug"]
        cache = HTML_DIR / f"{slug}.html"
        if cache.exists():
            html, status = cache.read_text(encoding="utf-8"), "cached"
        else:
            html, status = fetch(session, slug)
            if html:
                cache.write_text(html, encoding="utf-8")
            time.sleep(DELAY_SECONDS)
        if html is None:
            failed.append(f"{slug}\t{status}")
            rows.append({"slug": slug, "name": m["name"], "city": m["city"], "prov": m["prov"], "status": status,
                         "title": "", "categories": "", "website": "", "text_excerpt": ""})
        else:
            info = parse(html, slug)
            rows.append({"slug": slug, "name": m["name"], "city": m["city"], "prov": m["prov"], "status": status, **info})
        print(f"[{i}/{len(members)}] {m['name']}: {status}")

    with open(OUT / "companies.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "name", "city", "prov", "status", "title", "categories", "website", "text_excerpt"])
        w.writeheader()
        w.writerows(rows)
    (OUT / "failed.txt").write_text("\n".join(failed), encoding="utf-8")
    print(f"Done. {len(members) - len(failed)} pages saved, {len(failed)} failed. Now zip the 'out' folder.")


if __name__ == "__main__":
    main()
