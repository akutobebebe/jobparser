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
from rich.text import Text
from rich.rule import Rule
from rich.live import Live

from scrapers.base import JobSchema
from scrapers.djinni_scraper import DjinniScraper
from scrapers.dou_scraper import DOUScraper
from scrapers.linkedin_scraper import LinkedInScraper
from core.logger import setup_logger

logger = setup_logger(__name__)
console = Console()

# ── Палітра ────────────────────────────────────────────────────────────────
P  = "#a855f7"
P2 = "#7c3aed"
P3 = "#c084fc"
P4 = "#ede9fe"
DIM = "#6b7280"

# ── Questionary стиль ──────────────────────────────────────────────────────
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

# ── Піксельний змій (анімація) ─────────────────────────────────────────────
_SNAKE_HEAD = [
    r"    ▄██████▄    ",
    r"   ██  ◉◉  ██   ",
    r"   ██      ██   ",
    r"    ▀██████▀    ",
]

# хвіст: 2 рядки, зміщуються по горизонталі (wiggle)
_TAIL_FRAMES = [
    ["       ████     ", "      ██        "],
    ["        ████    ", "        ██      "],
    ["         ████   ", "          ██    "],
    ["        ████    ", "        ██      "],
    ["       ████     ", "      ██        "],
    ["      ████      ", "    ██          "],
    ["       ████     ", "      ██        "],
    ["        ████    ", "        ██      "],
]

# вертикальна позиція: скільки порожніх рядків зверху (bounce)
_BOUNCE_Y = [0, 0, 1, 2, 3, 4, 4, 3, 2, 1]
_MAX_Y    = max(_BOUNCE_Y)
# рядків у кадрі завжди однаково: max_y + head + tail + 1(sep) + 1(bar) + 1(empty)
_FRAME_H  = _MAX_Y + len(_SNAKE_HEAD) + 2 + 3
_BLANK    = " " * 22


def _build_live(frame: int, label: str, note: str, step: int, total: int) -> Text:
    y    = _BOUNCE_Y[frame % len(_BOUNCE_Y)]
    tail = _TAIL_FRAMES[frame % len(_TAIL_FRAMES)]

    t = Text(no_wrap=True)

    # порожні рядки зверху (bounce вгору = менше рядків, вниз = більше)
    for _ in range(y):
        t.append("  " + _BLANK + "\n")

    # голова
    for line in _SNAKE_HEAD:
        t.append("  " + line + "\n", style=f"bold {P}")

    # хвіст
    for line in tail:
        t.append("  " + line + "\n", style=P3)

    # порожні рядки знизу (щоб сума рядків була сталою)
    for _ in range(_MAX_Y - y):
        t.append("  " + _BLANK + "\n")

    # роздільник
    t.append("\n")

    # прогрес-бар
    pct  = step / total if total else 0
    done = int(pct * 32)
    t.append(f"  {label:<10}  ", style=P3)
    t.append("█" * done,       style=P)
    t.append("░" * (32 - done), style=f"dim {P2}")
    t.append(f"  {int(pct * 100):3d}%", style=f"dim {P3}")
    t.append(f"  {note}\n",    style=f"dim {DIM}")

    # нижній відступ (стала висота блоку)
    t.append("\n")

    return t


# ── Парсинг з анімацією ────────────────────────────────────────────────────
async def _scrape_animated(source: str) -> List[JobSchema]:
    steps: list[tuple[str, object]] = []
    if source in ("all", "djinni"):
        steps.append(("djinni", DjinniScraper()))
    if source in ("all", "dou"):
        steps.append(("dou", DOUScraper()))
    if source in ("all", "linkedin"):
        steps.append(("linkedin", LinkedInScraper()))

    total  = len(steps) + 1
    state  = {"frame": 0, "step": 0, "label": "starting", "note": "", "done": False}
    result: list[JobSchema] = []

    async def _animate(live: Live) -> None:
        while not state["done"]:
            state["frame"] += 1
            live.update(_build_live(
                state["frame"], state["label"],
                state["note"], state["step"], total,
            ), refresh=True)
            await asyncio.sleep(1 / 12)

    async def _scrape() -> None:
        batches: list[list[JobSchema]] = []
        for label, scraper in steps:
            state["label"] = label
            state["note"]  = "connecting..."
            await asyncio.sleep(1.5)
            state["note"]  = "fetching..."
            jobs = await scraper.scrape()
            state["note"]  = "parsing..."
            await asyncio.sleep(2.0)
            batches.append(jobs)
            state["step"] += 1
            state["note"] = f"{len(jobs)} found"
            await asyncio.sleep(1.0)

        state["label"] = "filter"
        state["note"]  = "dedup..."
        await asyncio.sleep(2.5)
        seen: set[str] = set()
        for batch in batches:
            for job in batch:
                if job.url not in seen:
                    seen.add(job.url)
                    result.append(job)
        state["step"] = total
        state["note"] = f"{len(result)} unique"
        await asyncio.sleep(1.0)
        state["done"] = True

    live_display = _build_live(0, "starting", "", 0, total)
    with Live(live_display, console=console, refresh_per_second=12, transient=True) as live:
        await asyncio.gather(_animate(live), _scrape())

    return result


def run_scrape(source: str) -> List[JobSchema]:
    return asyncio.run(_scrape_animated(source))


# ── Результати ─────────────────────────────────────────────────────────────
_NW = 3    # ширина колонки #
_TW = 44   # ширина колонки title
_CW = 22   # ширина колонки company


def _trunc(s: str, w: int) -> str:
    return (s[:w - 1] + "…") if len(s) > w else s


def print_results(jobs: List[JobSchema]) -> None:
    if not jobs:
        console.print(f"\n  [{P3}]no vacancies found.[/{P3}]\n")
        return

    by_source: dict[str, List[JobSchema]] = {}
    for job in jobs:
        by_source.setdefault(job.source, []).append(job)

    sep = "─" * (_NW + _TW + _CW + 8)

    for source, items in by_source.items():
        count = len(items)

        console.print()
        console.print(
            f"  [bold {P}]{source.upper()}[/bold {P}]"
            f"  [dim {P3}]·  {count} {'vacancy' if count == 1 else 'vacancies'}[/dim {P3}]"
        )
        console.print(f"  [dim {P2}]{sep}[/dim {P2}]")

        # Заголовок колонок
        hdr = Text("  ")
        hdr.append(f"{'#':<{_NW}}  ", style=f"dim {P3}")
        hdr.append(f"{'title':<{_TW}}  ", style=f"dim {P3}")
        hdr.append("company", style=f"dim {P3}")
        console.print(hdr)
        console.print(f"  [dim {P2}]{sep}[/dim {P2}]")
        console.print()

        for i, job in enumerate(items, 1):
            row = Text("  ")
            row.append(f"{i:<{_NW}}  ", style=f"dim {P2}")
            row.append(f"{_trunc(job.title, _TW):<{_TW}}  ", style=f"bold {P4}")
            row.append(_trunc(job.company, _CW), style=P3)
            console.print(row)

            indent = " " * (_NW + 4)
            url_t  = Text(f"  {indent}{job.url}", style=f"link {job.url} {P} underline")
            console.print(url_t)
            console.print()

    console.print(f"  [dim {P2}]{sep}[/dim {P2}]")
    total = len(jobs)
    console.print(
        f"\n  [bold {P}]found[/bold {P}]"
        f"  [bold {P4}]{total}[/bold {P4}]"
        f"  [dim {P3}]junior python {'vacancy' if total == 1 else 'vacancies'}[/dim {P3}]\n"
    )


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


# ── Меню ───────────────────────────────────────────────────────────────────
_SOURCES = [
    questionary.Choice("All sources",        value="all"),
    questionary.Choice("Djinni only",        value="djinni"),
    questionary.Choice("DOU only",           value="dou"),
    questionary.Choice("LinkedIn only",      value="linkedin"),
]


def main() -> None:
    print_header()

    while True:
        source = questionary.select(
            "source",
            choices=_SOURCES,
            style=_STYLE,
            instruction="(arrows · Enter)",
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
            logger.error(e, exc_info=True)
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
