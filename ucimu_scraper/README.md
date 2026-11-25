# UCIMU member scraper

Downloads the UCIMU catalog page of each Lombardy member (`lombardy_members.json`) and extracts the technology
categories (`taxonomy.json` maps category codes to names), the website and a text excerpt.

Run locally: `pip install requests beautifulsoup4 && python ucimu_scrape.py` (about 5 minutes, one request every 2 seconds).
Results go to `out/companies.csv`; the raw pages are kept in `out/html/`.
The GitHub Actions workflow in `.github/workflows/ucimu-scrape.yml` runs the same script on every push to this branch.
