# JOBPRSR

Terminal tool for finding junior Python vacancies on Djinni and DOU. Runs live — no database, no web UI.

```
     ██╗ ██████╗ ██████╗ ██████╗ ██████╗ ███████╗██████╗
     ██║██╔═══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
     ██║██║   ██║██████╔╝██████╔╝██████╔╝███████╗██████╔╝
██   ██║██║   ██║██╔══██╗██╔═══╝ ██╔══██╗╚════██║██╔══██╗
╚█████╔╝╚██████╔╝██████╔╝██║     ██║  ██║███████║██║  ██║
 ╚════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
```

## What it does

Scrapes **Djinni** and **DOU** for Python vacancies filtered to junior / strong junior / no experience level, then prints a clean table with clickable links in the terminal. No database, no persistence — just a fresh list every run.

Sources used:
- **Djinni** — `?primary_keyword=Python&exp_level=no_exp&exp_level=1y`
- **DOU** — RSS feeds `?category=Python&exp=0-1` and `?category=Python&exp=1-3`
- **LinkedIn** — public job search (requires Playwright Chromium, optional)

Junior filtering works on the **title only** (not the full description), which avoids false positives like a "Junior Python Developer" being tagged as senior because the word "senior" appeared somewhere in the job body.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # only needed for LinkedIn
```

Copy the optional env file if you want to override defaults:

```bash
cp .env.example .env
```

## Usage

```bash
python cli.py
```

Interactive menu appears:

```
? source
  > Djinni + DOU
    Djinni only
    DOU only
    LinkedIn only

? start scraping?  Yes
```

While scraping runs, a pixel-art snake animates with a progress bar. Results are printed as a table with full clickable URLs.

## Project structure

```
jobparser/
├── cli.py                    # entry point — interactive TUI
├── core/
│   ├── config.py             # settings (pydantic-settings, .env)
│   └── logger.py             # shared logger
└── scrapers/
    ├── base.py               # BaseScraper + JobSchema (Pydantic)
    ├── level.py              # is_junior() / detect_level() — title-first logic
    ├── djinni_scraper.py     # httpx + BeautifulSoup
    ├── dou_scraper.py        # httpx + xml.etree (RSS)
    └── linkedin_scraper.py   # Playwright Chromium (headless)
```

## Adding a new source

1. Create a class in `scrapers/` that extends `BaseScraper` and implements `scrape() -> List[JobSchema]`.
2. Add the source name to `valid_sources` in `scrapers/base.py:48`.
3. Wire it into `cli.py` (`_scrape_animated` and `_SOURCES`).

## LinkedIn on macOS

Playwright Chromium may be blocked by Gatekeeper on first run. Fix:

```bash
sudo xattr -cr ~/Library/Caches/ms-playwright/chromium-1091/chrome-mac/Chromium.app/
```

Or reinstall the browser:

```bash
playwright install chromium
```

If LinkedIn is unavailable the scraper returns an empty list and logs a warning — it does not crash the tool.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `REQUEST_TIMEOUT_SECONDS` | `30` | HTTP timeout for Djinni / DOU requests |
| `USER_AGENT` | Chrome/120 UA string | User-agent header |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

## Dependencies

| Package | Used for |
|---|---|
| `httpx` | Async HTTP — Djinni HTML, DOU RSS |
| `beautifulsoup4` + `lxml` | HTML parsing — Djinni |
| `pydantic` + `pydantic-settings` | Job schema validation, settings |
| `playwright` | Headless Chromium — LinkedIn |
| `rich` | Terminal output — table, progress bar, Live |
| `questionary` | Interactive menu |
| `pyfiglet` | ASCII art header |
