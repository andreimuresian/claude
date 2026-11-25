#!/usr/bin/env python3
"""
Scan the websites of the machine builders in builders.json for connectivity signals.

For each company it reads the home page plus up to MAX_PAGES internal pages that look relevant
(industry 4.0, service, software, news...), then counts keyword matches in four families:
  remote   - remote service / teleassistance / remote diagnostics
  iot_i40  - IoT, Industry 4.0, connected machines, OPC UA, MES, digital twin
  update   - software / firmware updates
  cyber    - cybersecurity, Cyber Resilience Act, NIS2, IEC 62443

Polite: checks robots.txt, one request every DELAY seconds per company, identifies itself.
Output (folder ./out_site): site_scan.csv, site_scan.json, text/<name>.txt (page text, capped)
"""
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
OUT = Path("out_site")
MAX_PAGES = 6
DELAY = 1.5
TIMEOUT = 15
MAX_BYTES = 1_500_000
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; personal-research-script)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8,de;q=0.7",
}

FAMILIES = {
    "remote": r"tele-?service|tele-?assistenza|assistenza (?:da )?remot|remote[ -](?:service|assistance|support|access|diagnos\w*|monitor\w*|control)|telediagnos\w*|teleservizio|fernwartung|fernzugriff|service remoto",
    "iot_i40": r"\biot\b|industry 4\.0|industria 4\.0|industrie 4\.0|smart factory|fabbrica intelligente|connected (?:machine|factory)s?|macchine? (?:interconness\w+|connesse)|interconnessi\w+|opc[ -]?ua|mtconnect|umati|\bmes\b|digital twin|gemello digitale",
    "update": r"software (?:update|upgrade)s?|aggiornament\w* (?:del )?software|firmware|over[- ]the[- ]air|\bota\b|aggiornamenti remoti",
    "cyber": r"cyber ?security|cyber[- ]resilience|\bcra\b|nis ?2\b|sicurezza informatica|iec ?62443|cybersicurezza",
}
FAMILY_RE = {k: re.compile(v, re.I) for k, v in FAMILIES.items()}
LINK_HINT = re.compile(
    r"industr\w*[ -]?4|4\.0|iot|servic|assistenza|support|software|digital|smart|connect|remote|news|cyber|secur|innovation|tecnolog|download|monitor",
    re.I)
SKIP_EXT = re.compile(r"\.(pdf|jpe?g|png|gif|svg|zip|rar|docx?|xlsx?|pptx?|mp4|mov|avi)(\?|$)", re.I)


def analyze(text):
    """Return per-family counts and up to 2 short evidence snippets per family."""
    res = {}
    for fam, rx in FAMILY_RE.items():
        hits = list(rx.finditer(text))
        snippets = []
        for m in hits[:2]:
            a, b = max(0, m.start() - 45), min(len(text), m.end() + 45)
            snippets.append(re.sub(r"\s+", " ", text[a:b]).strip())
        res[fam] = {"count": len(hits), "snippets": snippets}
    return res


def robots_ok(session, url):
    p = urlparse(url)
    rp = robotparser.RobotFileParser()
    try:
        r = session.get(f"{p.scheme}://{p.netloc}/robots.txt", headers=HEADERS, timeout=TIMEOUT)
        if r.status_code >= 400:
            return True
        rp.parse(r.text.splitlines())
    except requests.RequestException:
        return True
    return rp.can_fetch(HEADERS["User-Agent"], url)


def get_page(session, url):
    try:
        r = session.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if r.status_code != 200 or "html" not in r.headers.get("Content-Type", "").lower():
            return None, r.status_code
        raw = r.raw.read(MAX_BYTES, decode_content=True)
        enc = r.encoding or "utf-8"
        return raw.decode(enc, errors="replace"), 200
    except requests.RequestException as exc:
        return None, type(exc).__name__


def page_text_and_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    host = urlparse(base_url).netloc.replace("www.", "")
    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"]).split("#")[0]
        pu = urlparse(href)
        if pu.scheme not in ("http", "https") or SKIP_EXT.search(href):
            continue
        if pu.netloc.replace("www.", "") != host:
            continue
        label = f"{href} {a.get_text(' ', strip=True)}"
        if LINK_HINT.search(label) and href not in links:
            links.append(href)
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)), links


def scan_company(b):
    url = b["website"]
    name = b["name"]
    session = requests.Session()
    rec = {"name": name, "website": url, "domain": urlparse(url).netloc.replace("www.", ""),
           "tld": urlparse(url).netloc.split(".")[-1].lower(), "groups": b["groups"],
           "pages_read": 0, "status": "", "families": {}}
    if not robots_ok(session, url):
        rec["status"] = "robots_disallowed"
        return rec, ""
    html, status = get_page(session, url)
    time.sleep(DELAY)
    if html is None:
        rec["status"] = f"home_failed:{status}"
        return rec, ""
    text, links = page_text_and_links(html, url)
    texts = [text]
    rec["pages_read"] = 1
    for link in links[: MAX_PAGES - 1]:
        h2, s2 = get_page(session, link)
        time.sleep(DELAY)
        if h2:
            t2, _ = page_text_and_links(h2, link)
            texts.append(t2)
            rec["pages_read"] += 1
    full = "\n".join(texts)
    rec["status"] = "ok"
    rec["families"] = analyze(full)
    return rec, full


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "text").mkdir(exist_ok=True)
    builders = json.loads((HERE / "builders.json").read_text(encoding="utf-8"))

    def work(b):
        try:
            rec, full = scan_company(b)
        except Exception as exc:  # keep going whatever one site does
            rec, full = ({"name": b["name"], "website": b["website"], "domain": "", "tld": "", "groups": b["groups"],
                          "pages_read": 0, "status": f"error:{type(exc).__name__}", "families": {}}, "")
        safe = re.sub(r"[^A-Za-z0-9]+", "_", b["name"]).strip("_")
        if full:
            (OUT / "text" / f"{safe}.txt").write_text(full[:60000], encoding="utf-8")
        print(f"{b['name']}: {rec['status']} ({rec['pages_read']} pages)", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(work, builders))

    (OUT / "site_scan.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT / "site_scan.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["name", "website", "domain", "tld", "status", "pages_read", "groups"] +
                   [f"{k}_count" for k in FAMILIES] + [f"{k}_evidence" for k in FAMILIES])
        for r in results:
            fam = r["families"]
            w.writerow([r["name"], r["website"], r["domain"], r["tld"], r["status"], r["pages_read"],
                        ";".join(map(str, r["groups"]))] +
                       [fam.get(k, {}).get("count", "") for k in FAMILIES] +
                       [" || ".join(fam.get(k, {}).get("snippets", [])) for k in FAMILIES])
    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"Done: {ok}/{len(results)} sites scanned")


if __name__ == "__main__":
    main()
