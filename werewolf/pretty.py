"""A colourful console using the `rich` library. Importing this fails if rich isn't installed."""

from __future__ import annotations

from collections.abc import Sequence

from rich.console import Console as RichTerminal
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .console import Console, Style

STYLES = {
    "night": "bold bright_blue",
    "day": "bold yellow",
    "death": "bold red",
    "secret": "bold cyan",
    "error": "italic red",
}


class RichConsole(Console):
    def __init__(self) -> None:
        self.terminal = RichTerminal(highlight=False)

    def say(self, text: str = "", style: Style = None) -> None:
        # Text() keeps player names like "[Bob]" from being read as rich markup
        if style == "title":
            self.terminal.print(Panel(Text(text, style="bold magenta", justify="center")))
        elif style == "win":
            self.terminal.print(Panel(Text(text, style="bold green", justify="center")))
        else:
            self.terminal.print(Text(text, style=STYLES.get(style or "", "")))

    def ask(self, prompt: str) -> str:
        text = Text(prompt, style="bold")
        # Highlight the keys in numbered choices like "(1 Ann, 2 Bob, s skip)"
        text.highlight_regex(r"(?:(?<=\()|(?<=, ))(?:\d+|s)(?= )", "cyan")
        return self.terminal.input(text)

    def table(self, title: str, headers: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
        table = Table(title=title, title_style="bold", header_style="bold cyan")
        for header in headers:
            table.add_column(header)
        for row in rows:
            table.add_row(*(Text(str(cell)) for cell in row))
        self.terminal.print(table)
