"""
JOBPRSR — junior python vacancy finder
"""

import asyncio
import sys
from typing import List

import pyfiglet
import questionary
from questionary import Style
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.padding import Padding
from rich.progress import (
    Progress, SpinnerColumn, BarColumn,
    TextColumn, TaskProgressColumn, TimeElapsedColumn,
)
from rich import box

from scrapers.base import JobSchema
from scrapers.djinni_scraper import DjinniScraper
from scrapers.dou_scraper import DOUScraper
from core.logger import setup_logger

logger = setup_logger(__name__)
console = Console()

# ── Палітра ────────────────────────────────────────────────────────────────
P  = "#a855f7"   # основний фіолетовий
P2 = "#7c3aed"   # темний фіолетовий
P3 = "#c084fc"   # світлий фіолетовий
P4 = "#ede9fe"   # лавандовий (текст)
DIM = "#6b7280"

# ── Стиль questionary ──────────────────────────────────────────────────────
_STYLE = Style([
    ("qmark",       f"fg:{P} bold"),
    ("question",    f"fg:{P4} bold"),
    ("answer",      f"fg:{P3} bold"),
    ("pointer",     f"fg:{P} bold"),
    ("highlighted", f"fg:{P} bold"),
    ("selected",    f"fg:{P3}"),
    ("separator",   f"fg:{P2}"),
    ("instruction", f"fg:{DIM} italic"),
    ("text",        f"fg:{P4}"),
])

# ── Заголовок ──────────────────────────────────────────────────────────────
def print_header() -> None:
    banner = pyfiglet.figlet_format("JOBPRSR", font="ansi_shadow")
    console.print()
    for line in banner.splitlines():
        console.print(f"  [bold {P}]{line}[/bold {P}]")

    console.print(f"  [dim {P3}]junior python vacancy finder  ·  djinni + dou[/dim {P3}]")
    console.print()
    console.print(Rule(style=P2))
    console.print()


# ── Парсинг ────────────────────────────────────────────────────────────────
def _make_progress() -> Progress:
    return Progress(
        SpinnerColumn(spinner_name="dots2", style=f"bold {P}"),
        TextColumn("[{task.fields[label]}]", style=f"{P3}"),
        BarColumn(
            bar_width=28,
            style=f"dim {P2}",
            complete_style=P,
            finished_style=P3,
        ),
        TaskProgressColumn(style=f"dim {P3}"),
        TextColumn("[dim]{task.fields[note]}[/dim]", style=DIM),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


async def _scrape_with_progress(source: str, progress: Progress) -> List[JobSchema]:
    steps: list[tuple[str, object]] = []  # (label, scraper_or_None)

    if source in ("all", "djinni"):
        steps.append(("djinni", DjinniScraper()))
    if source in ("all", "dou"):
        steps.append(("dou   ", DOUScraper()))

    # крок "фільтрація" — фіксований останній
    total_steps = len(steps) + 1

    main_task = progress.add_task(
        "", total=total_steps, label="scraping", note=""
    )

    batches: list[list[JobSchema]] = []
    for label, scraper in steps:
        progress.update(main_task, label=label, note="fetching...")
        jobs = await scraper.scrape()
        batches.append(jobs)
        progress.update(main_task, advance=1, note=f"{len(jobs)} found")

    # фільтрація / дедуплікація
    progress.update(main_task, label="filter", note="dedup...")
    seen: set[str] = set()
    result: list[JobSchema] = []
    for batch in batches:
        for job in batch:
            if job.url not in seen:
                seen.add(job.url)
                result.append(job)
    progress.update(main_task, advance=1, note=f"{len(result)} unique")

    return result


def run_scrape(source: str) -> List[JobSchema]:
    with _make_progress() as progress:
        return asyncio.run(_scrape_with_progress(source, progress))


# ── Результати ─────────────────────────────────────────────────────────────
def print_results(jobs: List[JobSchema]) -> None:
    if not jobs:
        console.print(f"\n  [{P3}]no vacancies found.[/{P3}]\n")
        return

    by_source: dict[str, List[JobSchema]] = {}
    for job in jobs:
        by_source.setdefault(job.source, []).append(job)

    for source, items in by_source.items():
        label = source.upper()
        count = len(items)

        console.print()
        console.print(
            f"  [bold {P}]{label}[/bold {P}]"
            f"  [dim {P3}]{count} {'vacancy' if count == 1 else 'vacancies'}[/dim {P3}]"
        )
        console.print(f"  [dim {P2}]{'─' * 62}[/dim {P2}]")

        table = Table(
            box=None,
            show_header=True,
            show_edge=False,
            show_lines=False,
            padding=(0, 2, 0, 2),
            header_style=f"dim {P3}",
            expand=True,
        )
        table.add_column("  #",      style=f"dim {P2}",  width=4,  no_wrap=True)
        table.add_column("title",    style=f"bold {P4}", ratio=38)
        table.add_column("company",  style=f"{P3}",      ratio=22)
        table.add_column("url",      style=f"dim {P}",   ratio=40, no_wrap=False)

        for i, job in enumerate(items, 1):
            link = Text(job.url, style=f"link {job.url} {P} underline")
            table.add_row(f"  {i}", job.title, job.company, link)

        console.print(Padding(table, (0, 0, 0, 2)))

    console.print()
    console.print(Rule(style=P2))
    total = len(jobs)
    console.print(
        f"\n  [bold {P}]found[/bold {P}]"
        f"  [bold {P4}]{total}[/bold {P4}]"
        f"  [dim {P3}]junior python {'vacancy' if total == 1 else 'vacancies'}[/dim {P3}]"
    )
    console.print()


# ── Меню ───────────────────────────────────────────────────────────────────
_SOURCES = [
    questionary.Choice("Djinni + DOU",  value="all"),
    questionary.Choice("Djinni only",   value="djinni"),
    questionary.Choice("DOU only",      value="dou"),
]


def main() -> None:
    print_header()

    while True:
        source = questionary.select(
            "source",
            choices=_SOURCES,
            style=_STYLE,
            instruction="(use arrows, Enter to confirm)",
        ).ask()

        if source is None:
            console.print(f"\n  [dim {DIM}]bye.[/dim {DIM}]\n")
            sys.exit(0)

        console.print()

        go = questionary.confirm(
            "start scraping?",
            default=True,
            style=_STYLE,
        ).ask()

        if not go:
            console.print(f"\n  [dim {DIM}]cancelled.[/dim {DIM}]\n")
            sys.exit(0)

        console.print()

        try:
            jobs = run_scrape(source)
        except KeyboardInterrupt:
            console.print(f"\n  [dim {DIM}]interrupted.[/dim {DIM}]\n")
            sys.exit(0)
        except Exception as e:
            console.print(f"\n  [bold red]error:[/bold red] {e}\n")
            sys.exit(1)

        print_results(jobs)

        again = questionary.confirm(
            "run again?",
            default=False,
            style=_STYLE,
        ).ask()

        if not again:
            console.print(f"  [dim {DIM}]bye.[/dim {DIM}]\n")
            break

        console.print()
        console.print(Rule(style=P2))
        console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(f"\n  [dim {DIM}]bye.[/dim {DIM}]\n")
        sys.exit(0)
