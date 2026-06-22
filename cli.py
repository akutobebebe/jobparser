"""
Junior Python Job Finder — Djinni + DOU
"""

import asyncio
import sys
from typing import List

import questionary
from questionary import Style
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from scrapers.base import JobSchema
from scrapers.djinni_scraper import DjinniScraper
from scrapers.dou_scraper import DOUScraper
from core.logger import setup_logger

logger = setup_logger(__name__)

console = Console()

# ── Стиль questionary ──────────────────────────────────────────────────────
_Q_STYLE = Style([
    ("qmark",        "fg:#00d7ff bold"),
    ("question",     "bold"),
    ("answer",       "fg:#00ff87 bold"),
    ("pointer",      "fg:#00d7ff bold"),
    ("highlighted",  "fg:#00d7ff bold"),
    ("selected",     "fg:#00ff87"),
    ("separator",    "fg:#444444"),
    ("instruction",  "fg:#888888 italic"),
])

# ── Джерела ────────────────────────────────────────────────────────────────
SOURCE_CHOICES = [
    questionary.Choice("🔵  Djinni + DOU  (обидва)", value="all"),
    questionary.Choice("🟣  Тільки Djinni",           value="djinni"),
    questionary.Choice("🟠  Тільки DOU",              value="dou"),
]


# ── Парсинг ────────────────────────────────────────────────────────────────
async def _scrape(source: str) -> List[JobSchema]:
    scrapers = []
    if source in ("all", "djinni"):
        scrapers.append(DjinniScraper())
    if source in ("all", "dou"):
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


def run_scrape(source: str) -> List[JobSchema]:
    with Progress(
        SpinnerColumn(spinner_name="dots", style="cyan"),
        TextColumn("[cyan]Парсимо вакансії…"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("", total=None)
        jobs = asyncio.run(_scrape(source))
    return jobs


# ── Відображення результатів ───────────────────────────────────────────────
def _source_color(source: str) -> str:
    return {"djinni": "bright_magenta", "dou": "bright_yellow"}.get(source, "white")


def print_results(jobs: List[JobSchema]) -> None:
    if not jobs:
        console.print(Panel("[yellow]Вакансій не знайдено.[/yellow]", border_style="yellow"))
        return

    by_source: dict[str, List[JobSchema]] = {}
    for job in jobs:
        by_source.setdefault(job.source, []).append(job)

    for source, items in by_source.items():
        color = _source_color(source)

        table = Table(
            box=box.ROUNDED,
            border_style=color,
            header_style=f"bold {color}",
            show_lines=True,
            expand=True,
            title=f"[bold {color}]{source.upper()}[/bold {color}]  [{color}]{len(items)} вакансій[/{color}]",
            title_justify="left",
        )
        table.add_column("#",         style="dim",        width=3,  no_wrap=True)
        table.add_column("Назва",     style="bold white", ratio=40)
        table.add_column("Компанія",  style="cyan",       ratio=25)
        table.add_column("Посилання", style="bright_blue", ratio=35)

        for i, job in enumerate(items, 1):
            link = Text(job.url, style=f"link {job.url} bright_blue underline")
            table.add_row(str(i), job.title, job.company, link)

        console.print(table)
        console.print()

    total = len(jobs)
    console.print(
        Panel(
            f"[bold green]✓  Знайдено [bright_white]{total}[/bright_white] junior Python-вакансій[/bold green]",
            border_style="green",
            expand=False,
        )
    )


# ── Головне меню ───────────────────────────────────────────────────────────
def main() -> None:
    console.print()
    console.print(Panel(
        "[bold cyan]Junior Python Job Finder[/bold cyan]\n"
        "[dim]Djinni · DOU  —  тільки junior / strong junior / без досвіду[/dim]",
        border_style="cyan",
        expand=False,
    ))
    console.print()

    while True:
        # 1. Вибір джерела
        source = questionary.select(
            "Оберіть джерело:",
            choices=SOURCE_CHOICES,
            style=_Q_STYLE,
            use_shortcuts=False,
        ).ask()

        if source is None:           # Ctrl+C
            console.print("[dim]Скасовано.[/dim]")
            sys.exit(0)

        # 2. Підтвердження — кнопка «Парсити»
        go = questionary.confirm(
            "Запустити парсинг?",
            default=True,
            style=_Q_STYLE,
        ).ask()

        if not go:
            console.print("[dim]Скасовано.[/dim]")
            sys.exit(0)

        # 3. Парсинг
        console.print()
        try:
            jobs = run_scrape(source)
        except KeyboardInterrupt:
            console.print("\n[dim]Перервано.[/dim]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Помилка:[/red] {e}")
            sys.exit(1)

        # 4. Результати
        console.print()
        print_results(jobs)
        console.print()

        # 5. Повторити або вийти
        again = questionary.confirm(
            "Зробити ще один запит?",
            default=False,
            style=_Q_STYLE,
        ).ask()

        if not again:
            console.print("[dim]До побачення![/dim]")
            break

        console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Перервано.[/dim]")
        sys.exit(0)
