"""
Junior Python Job Finder — Djinni + DOU
Usage:
  python cli.py                   # обидва джерела
  python cli.py --source djinni   # тільки Djinni
  python cli.py --source dou      # тільки DOU
  python cli.py --limit 20        # обмежити кількість результатів
"""

import asyncio
import argparse
import sys
from typing import List

from scrapers.base import JobSchema
from scrapers.djinni_scraper import DjinniScraper
from scrapers.dou_scraper import DOUScraper
from core.logger import setup_logger

logger = setup_logger(__name__)

# ── ANSI-кольори (вимикаються якщо stdout не tty) ──────────────────────────
_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


BOLD   = lambda t: _c("1", t)
CYAN   = lambda t: _c("36", t)
GREEN  = lambda t: _c("32", t)
YELLOW = lambda t: _c("33", t)
DIM    = lambda t: _c("2", t)


# ── OSC-8 гіперлінк (клікабельний у більшості сучасних терміналів) ─────────
def hyperlink(url: str, label: str | None = None) -> str:
    if not _USE_COLOR:
        return url
    text = label or url
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


# ── Форматування одного запису ─────────────────────────────────────────────
def format_job(job: JobSchema) -> str:
    title_line = f"  {BOLD(job.title)} {DIM('—')} {job.company}"
    url_line   = f"    {hyperlink(job.url, GREEN(job.url))}"
    return f"{title_line}\n{url_line}"


# ── Основна логіка ─────────────────────────────────────────────────────────
async def collect_jobs(source: str | None) -> List[JobSchema]:
    scrapers = []
    if source in (None, "djinni"):
        scrapers.append(DjinniScraper())
    if source in (None, "dou"):
        scrapers.append(DOUScraper())

    results = await asyncio.gather(*(s.scrape() for s in scrapers))

    seen: set[str] = set()
    jobs: List[JobSchema] = []
    for batch in results:
        for job in batch:
            if job.url not in seen:
                seen.add(job.url)
                jobs.append(job)
    return jobs


def print_results(jobs: List[JobSchema], limit: int | None) -> None:
    if limit:
        jobs = jobs[:limit]

    if not jobs:
        print(YELLOW("Вакансій не знайдено."))
        return

    by_source: dict[str, List[JobSchema]] = {}
    for job in jobs:
        by_source.setdefault(job.source, []).append(job)

    for source, items in by_source.items():
        header = CYAN(BOLD(f"=== {source.upper()} ({len(items)}) ==="))
        print(f"\n{header}")
        for job in items:
            print(format_job(job))

    total = len(jobs)
    print(f"\n{BOLD(GREEN(f'Знайдено {total} junior Python-вакансій.'))}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Знайти junior Python-вакансії на Djinni та DOU",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        choices=["djinni", "dou"],
        default=None,
        help="Показати лише одне джерело (за замовчуванням — обидва)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Показати не більше N результатів",
    )
    args = parser.parse_args()

    print(BOLD(CYAN("Шукаємо junior Python-вакансії…")))

    try:
        jobs = asyncio.run(collect_jobs(args.source))
    except KeyboardInterrupt:
        print("\nПерервано.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Помилка: {e}", exc_info=True)
        print(f"Помилка: {e}", file=sys.stderr)
        sys.exit(1)

    print_results(jobs, args.limit)


if __name__ == "__main__":
    main()
