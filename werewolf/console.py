"""Terminal input and output, kept apart from the game rules so tests can script it."""

from __future__ import annotations

import sys
import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal, Protocol, overload

if TYPE_CHECKING:
    from .game import Player


class ConsoleLike(Protocol):
    def say(self, text: str = "") -> None: ...
    def ask(self, prompt: str) -> str: ...
    def clear(self) -> None: ...
    def discuss(self, seconds: int) -> None: ...


class Console:
    """Reads from and writes to the terminal."""

    def say(self, text: str = "") -> None:
        print(text)

    def ask(self, prompt: str) -> str:
        return input(prompt)

    def clear(self) -> None:
        # Clear the screen and the scrollback so the next player can't scroll up
        print("\033[H\033[2J\033[3J", end="", flush=True)

    def discuss(self, seconds: int) -> None:
        """Show a countdown while players talk. Enter ends it early."""
        self.say(f"Discuss! You have {format_time(seconds)} to find the werewolves. "
                 "Press Enter to vote early.")
        end = time.monotonic() + seconds
        while (left := end - time.monotonic()) > 0:
            print(f"\r  {format_time(round(left))} left ", end="", flush=True)
            if _enter_pressed(min(1.0, left)):
                print("\r  Discussion over.   ")
                return
        print("\r  Time's up!         ")


def format_time(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


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


def ask_int(console: ConsoleLike, prompt: str, low: int, high: int,
            default: int | None = None) -> int:
    while True:
        answer = console.ask(prompt).strip()
        if not answer and default is not None:
            return default
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        console.say(f"Please enter a whole number from {low} to {high}.")


def ask_yes_no(console: ConsoleLike, prompt: str) -> bool:
    while True:
        answer = console.ask(f"{prompt} (yes/no): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        console.say("Please answer yes or no.")


@overload
def ask_player(console: ConsoleLike, prompt: str, candidates: Sequence[Player],
               allow_skip: Literal[False] = False) -> Player: ...
@overload
def ask_player(console: ConsoleLike, prompt: str, candidates: Sequence[Player],
               allow_skip: Literal[True]) -> Player | None: ...
def ask_player(console: ConsoleLike, prompt: str, candidates: Sequence[Player],
               allow_skip: bool = False) -> Player | None:
    """Ask for one of `candidates` by name (any case). Returns None if the player skips."""
    by_name = {p.name.lower(): p for p in candidates}
    choices = ", ".join(p.name for p in candidates)
    if allow_skip:
        choices += ", or skip"

    while True:
        answer = console.ask(f"{prompt} [{choices}]: ").strip().lower()
        if allow_skip and answer == "skip":
            return None
        if answer in by_name:
            return by_name[answer]
        console.say("That isn't one of the choices.")
