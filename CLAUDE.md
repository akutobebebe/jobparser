# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the interactive CLI scraper (no DB persistence)
python cli.py

# Run the Streamlit web UI (with DB persistence at jobs.db)
streamlit run app.py

# Run tests
pytest tests/ -v

# Run a single test file
pytest tests/test_validators.py -v
```

**Setup:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

> Note: `rich`, `questionary`, `pyfiglet` are used by `cli.py` but missing from `requirements.txt` — install them separately if needed.

## Architecture

This is a Python job aggregator that scrapes Djinni.co and DOU.ua for junior Python developer vacancies. It has two independent interfaces: a Rich/questionary CLI and a Streamlit web UI.

### Data flow

```
Scraper → JobSchema (Pydantic validation) → [CLI: display only | Streamlit: SQLite via SQLAlchemy]
```

### Key modules

**`scrapers/base.py`** — `BaseScraper` abstract class (requires `scrape() → List[JobSchema]` and `get_source_url()`) + `JobSchema` Pydantic model. All scrapers call `self.validate_job(dict)` before appending results.

**`scrapers/level.py`** — Junior detection logic used by both scrapers:
- `is_junior(title)` — gate function; returns `False` if title contains senior/lead/middle keywords. If `False`, the job is skipped entirely.
- `detect_level(title, description)` — classifies as `"junior"`, `"middle"`, `"senior"`, or `None`.

**`scrapers/djinni_scraper.py`** — Uses `httpx` + `BeautifulSoup` to parse HTML from Djinni's filtered job listing page (`?primary_keyword=Python&exp_level=no_exp&exp_level=1y`).

**`scrapers/dou_scraper.py`** — Uses `httpx` + `xml.etree.ElementTree` to parse DOU's RSS feeds (`?category=Python&exp=0-1` and `exp=1-3`). Strips query strings from URLs to deduplicate. Parses company from RSS title format `"Job Title в Company Name"`.

**`scrapers/linkedin_scraper.py`** — Uses async Playwright (Chromium) to load LinkedIn's public job search page (no login). Targets `?keywords=Python&f_E=1%2C2&location=Ukraine` (f_E=1 Internship, f_E=2 Entry level). LinkedIn CSS selectors (`base-search-card__title`, `base-search-card__subtitle`) may break when LinkedIn updates their layout — the scraper returns an empty list gracefully in that case. Requires `playwright install chromium` after pip install.

**`core/config.py`** — Pydantic `Settings` loaded from `.env`. Access via `get_settings()` (cached with `@lru_cache`). Key flags: `enable_djinni`, `enable_dou`.

**`database/`** — SQLAlchemy + SQLite. `models.py` defines `Job` (unique on `url`) and `Source`. `connection.py` creates engine with `StaticPool` for SQLite thread safety. `crud.py` provides standard CRUD; `get_job_by_url` is used to avoid duplicate inserts.

**`cli.py`** — Scrapes and displays results in the terminal using Rich tables. Does **not** persist to the database. Deduplicates by URL in memory across sources.

**`app.py`** — Streamlit UI that initializes the DB on first load, runs scrapers async via `asyncio.run()`, and saves results to `jobs.db`.

### Adding a new scraper

1. Create a class in `scrapers/` extending `BaseScraper`, implement `scrape()` and `get_source_url()`.
2. Add the source name to the `valid_sources` set in `JobSchema.validate_source` (`scrapers/base.py:49`).
3. Wire it into `cli.py` and/or `app.py`.
