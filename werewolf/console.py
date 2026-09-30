"""Terminal input and output, kept apart from the game rules so tests and bots can stand in.

Parsing player input is done by pure functions that return an Either: Right(value) for a valid
answer, or Left(message) explaining what was wrong. BaseConsole keeps asking until it gets a Right.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Literal, TypeVar, overload

from .either import Either, Left, Right, ensure

if TYPE_CHECKING:
    from .game import Player

T = TypeVar("T")

# Styles the game uses; each console decides how (or whether) to show them
Style = Literal["title", "night", "day", "death", "secret", "win", "error"] | None

YES_NO = {"y": True, "yes": True, "n": False, "no": False}
SKIP_WORDS = ("s", "skip")


# --- Parsing input ----------------------------------------------------------

def parse_int(answer: str, low: int, high: int, default: int | None = None) -> Either[str, int]:
    text = answer.strip()
    if not text and default is not None:
        return Right(default)
    error = f"Please enter a whole number from {low} to {high}."
    return (Right(text)
            .then(ensure(str.isdigit, error))
            .map(int)
            .then(ensure(lambda n: low <= n <= high, error)))


def parse_yes_no(answer: str) -> Either[str, bool]:
    text = answer.strip().lower()
    return Right(YES_NO[text]) if text in YES_NO else Left("Please answer yes or no.")


def parse_player(answer: str, candidates: Sequence[Player],
                 allow_skip: bool = False) -> Either[str, Player | None]:
    """Accepts a player's name (any case), their number in the list, or skip if allowed."""
    text = answer.strip().lower()
    if allow_skip and text in SKIP_WORDS:
        return Right(None)
    if text.isdigit():
        number = int(text)
        if 1 <= number <= len(candidates):
            return Right(candidates[number - 1])
        return Left(f"Pick a number from 1 to {len(candidates)}.")
    by_name = {p.name.lower(): p for p in candidates}
    return Right(by_name[text]) if text in by_name else Left("That isn't one of the choices.")


def parse_name(answer: str, taken: Sequence[str]) -> Either[str, str]:
    name = answer.strip()
    return (Right(name)
            .then(ensure(bool, "Names can't be empty."))
            .then(ensure(lambda n: not n.isdigit(), "Names can't be just a number."))
            .then(ensure(lambda n: n.lower() not in SKIP_WORDS,
                         f"'{name}' is used for skipping, so pick another name."))
            .then(ensure(lambda n: n.lower() not in (t.lower() for t in taken),
                         f"{name} is already taken.")))


def choice_prompt(prompt: str, candidates: Sequence[Player], allow_skip: bool) -> str:
    choices = [f"{i} {p.name}" for i, p in enumerate(candidates, 1)]
    if allow_skip:
        choices.append("s skip")
    return f"{prompt} ({', '.join(choices)}): "


def format_time(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


# --- Consoles ---------------------------------------------------------------

class BaseConsole:
    """Everything the game needs from a console. Subclasses provide say and ask."""

    def say(self, text: str = "", style: Style = None) -> None:
        raise NotImplementedError

    def ask(self, prompt: str) -> str:
        raise NotImplementedError

    def clear(self) -> None:
        pass

    def discuss(self, seconds: int) -> None:
        pass

    def table(self, title: str, headers: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
        self.say(f"{title}:")
        cells = [[str(c) for c in row] for row in [headers, *rows]]
        widths = [max(len(row[i]) for row in cells) for i in range(len(headers))]
        for row in cells:
            self.say("  " + "  ".join(c.ljust(w) for c, w in zip(row, widths, strict=True)).rstrip())

    def ask_until_valid(self, prompt: str, parse: Callable[[str], Either[str, T]]) -> T:
        while True:
            result = parse(self.ask(prompt))
            if isinstance(result, Right):
                return result.value
            self.say(result.error, style="error")

    def number(self, prompt: str, low: int, high: int, default: int | None = None) -> int:
        return self.ask_until_valid(prompt, lambda a: parse_int(a, low, high, default))

    def confirm(self, prompt: str, who: Player | None = None) -> bool:
        """A yes/no question. `who` is the player answering, if it's one player's decision."""
        return self.ask_until_valid(f"{prompt} (yes/no): ", parse_yes_no)

    @overload
    def choose_player(self, prompt: str, candidates: Sequence[Player],
                      allow_skip: Literal[False] = False, who: Player | None = None) -> Player: ...
    @overload
    def choose_player(self, prompt: str, candidates: Sequence[Player],
                      allow_skip: Literal[True], who: Player | None = None) -> Player | None: ...
    def choose_player(self, prompt: str, candidates: Sequence[Player],
                      allow_skip: bool = False, who: Player | None = None) -> Player | None:
        """Pick one of `candidates`. Returns None if skipping is allowed and chosen."""
        return self.ask_until_valid(choice_prompt(prompt, candidates, allow_skip),
                                    lambda a: parse_player(a, candidates, allow_skip))


class Console(BaseConsole):
    """Plain terminal output."""

    def say(self, text: str = "", style: Style = None) -> None:
        print(text)

    def ask(self, prompt: str) -> str:
        return input(prompt)

    def clear(self) -> None:
        # Clear the screen and the scrollback so the next player can't scroll up
        print("\033[H\033[2J\033[3J", end="", flush=True)

    def discuss(self, seconds: int) -> None:
        """Show a countdown while players talk. Enter ends it early."""
        self.say(f"Discuss! You have {format_time(seconds)} to find the werewolves. "
                 "Press Enter to vote early.", style="day")
        end = time.monotonic() + seconds
        while (left := end - time.monotonic()) > 0:
            print(f"\r  {format_time(round(left))} left ", end="", flush=True)
            if _enter_pressed(min(1.0, left)):
                print("\r  Discussion over.   ")
                return
        print("\r  Time's up!         ")


def _enter_pressed(timeout: float) -> bool:
    """Wait up to `timeout` seconds for Enter without blocking past it."""
    if sys.platform == "win32":
        import msvcrt
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if msvcrt.kbhit() and msvcrt.getwch() in "\r\n":
                return True
            time.sleep(0.05)
        return False

    import select
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        sys.stdin.readline()
        return True
    return False


def make_console() -> BaseConsole:
    """The nicest console available: colours with `rich` if it's installed, plain otherwise."""
    try:
        from .pretty import RichConsole
    except ImportError:
        return Console()
    return RichConsole()
